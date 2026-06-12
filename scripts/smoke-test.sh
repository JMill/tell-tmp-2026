#!/usr/bin/env bash
# smoke-test.sh
#
# End-to-end smoke test for TELL. Runs the known-good set of commands that
# together verify: Python CLI works, Neon connection works, Wayback adapter
# works, Blob upload works, and the dashboard builds.
#
# This is the repeatable version of the manual walkthrough in
# dev/tell/docs/getting-started.md. Run it after any non-trivial change to
# the ingestion stack or schema. If something fails, the getting-started doc
# has a "Quirks and gotchas" section that covers most known failure modes.
#
# Prerequisites:
#   - You've run `vercel env pull .env.local --yes` from dev/tell/
#   - `pnpm install` and `uv sync` have been run
#   - The Neon schema is pushed (`pnpm --filter @tells-fyi/db exec drizzle-kit push --force`)
#
# Usage:
#   bash scripts/smoke-test.sh
#
# Exit codes:
#   0 — all checks passed
#   1 — any check failed
set -euo pipefail

# Always run from the pipeline root regardless of where the script was invoked.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PIPELINE_ROOT"

CORPUS="${SMOKE_TEST_CORPUS:-smoke-test-$(date -u +%Y-%m-%d)}"
SMOKE_URL="${SMOKE_TEST_URL:-https://en.wikipedia.org/wiki/2024_United_States_drone_sightings}"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
blue() { printf '\033[34m%s\033[0m\n' "$*"; }

fail() {
  red "FAIL: $*"
  exit 1
}

step() {
  blue "→ $*"
}

# 1. Environment sanity
step "Checking .env.local exists"
[[ -f .env.local ]] || fail ".env.local missing. Run: vercel env pull .env.local --yes"
green "✓ .env.local present"

# 2. Python CLI reachable
step "Checking signals CLI is installed and runnable"
uv run signals --help >/dev/null || fail "signals CLI failed to run. Run: uv sync"
green "✓ signals CLI runnable"

# 3. Unit tests pass
step "Running Python unit tests"
uv run pytest python/signals_core/tests/ python/signals_ingest/tests/ -q || fail "Python unit tests failed"
green "✓ Python unit tests pass"

# 4. TypeScript typecheck
step "Running TypeScript typecheck on @tells-fyi/db and dashboard"
pnpm --filter @tells-fyi/db exec tsc --noEmit || fail "@tells-fyi/db typecheck failed"
pnpm --filter dashboard exec tsc --noEmit || fail "dashboard typecheck failed"
green "✓ TypeScript typecheck passes"

# 5. Neon connectivity via the status command
step "Checking Neon connectivity"
uv run signals ingest status >/dev/null || fail "signals ingest status failed. Check DATABASE_URL in .env.local"
green "✓ Neon reachable"

# 6. Ingest a known URL via the Wayback adapter
step "Ingesting a known URL via the Wayback Machine"
step "  corpus: $CORPUS"
step "  url:    $SMOKE_URL"
INGEST_OUTPUT=$(uv run signals ingest wayback --url "$SMOKE_URL" --corpus "$CORPUS" 2>&1) || {
  echo "$INGEST_OUTPUT"
  fail "Wayback ingest failed. Check the Quirks section in docs/getting-started.md"
}
echo "$INGEST_OUTPUT"
echo "$INGEST_OUTPUT" | grep -q "Blob URL" || fail "Ingest output did not include a Blob URL — upload may have failed"
echo "$INGEST_OUTPUT" | grep -q "Document ID" || fail "Ingest output did not include a Document ID — Neon insert may have failed"
green "✓ End-to-end ingest (Wayback → trafilatura → Blob → Neon) succeeded"

# 7. Verify the document shows up in the count
step "Verifying corpus count"
COUNT=$(uv run signals ingest status --corpus "$CORPUS" 2>&1 | grep -oE '^[0-9]+' | head -1 || echo "0")
[[ "$COUNT" -ge 1 ]] || fail "Expected ≥1 document in $CORPUS, got $COUNT"
green "✓ $COUNT document(s) in $CORPUS"

# 8. Dashboard production build
step "Building the Next.js dashboard"
pnpm --filter dashboard build 2>&1 | tail -15 || fail "Next.js build failed"
green "✓ Dashboard builds cleanly"

echo
green "=============================="
green "  Smoke test: ALL CHECKS PASS "
green "=============================="
echo
echo "Corpus used: $CORPUS"
echo "To re-run against a different corpus, set SMOKE_TEST_CORPUS env var."
echo "To ingest a different URL, set SMOKE_TEST_URL env var."
