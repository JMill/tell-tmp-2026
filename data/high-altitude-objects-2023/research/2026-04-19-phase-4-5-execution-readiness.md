# Phase 4-5 Execution-Readiness Memo

**Compiled:** 2026-04-19
**For:** JMill, as operator of the Phase 4 ingestion run and Phase 5 signal computation

## Purpose

This memo documents what an operator needs to run Phase 4 (corpus ingestion) and Phase 5 (signal computation) end-to-end against the `high-altitude-objects-2023` investigation. It names blockers that must be resolved before execution and supplies the exact commands to use once blockers are clear.

This memo is a research-and-documentation artifact. It does not execute any ingestion, signal computation, or database writes. Those steps require Vercel and Neon credentials that are not in the session context and must be performed by a human operator.

## Prerequisites from prior phases

1. Phase 0 dossiers committed at `research/2026-04-19-verified-events.md` and `research/2026-04-19-fourth-fifth-object-anomalies.md`.
2. Phase 1 `narratives.yaml` committed with 8 slugs mapped to H1-H5.
3. Phase 2 `timeline.yaml` committed with 37 canonical events.
4. Phase 3 `seed-urls.yaml` committed with 98 seeds across 7 source kinds.
5. JMill has reviewed and annotated all four files and resolved any `[CITE-NEEDED]` markers that block canonical-date audit.

## Phase 4 readiness

### Environment prerequisites

- `vercel env pull` has produced a valid `.env.local` at `dev/tell/.env.local` containing at minimum `DATABASE_URL`, `BLOB_READ_WRITE_TOKEN`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY`.
- Python 3.12+ with `uv` installed and the workspace synced with `uv sync`.
- The Neon branch for the new corpus version (proposed: `high-altitude-objects-2023-YYYY-MM-DD`) has been created; the default branch configuration in `drizzle.config.ts` is expected to pick it up via `DATABASE_URL`.
- The Vercel Blob store is writable under the corpus-version key prefix.

### Command sequence

```
cd /home/user/praxis-deng/dev/tell

# sanity check: seed file parses and resolves to narratives.yaml
uv run python -c "import yaml; y=yaml.safe_load(open('data/high-altitude-objects-2023/seed-urls.yaml')); print('seeds=', len(y['seeds']))"

# pin a corpus version string for this run
export CORPUS_VERSION=high-altitude-objects-2023-$(date -u +%Y-%m-%d)

# dry-run verification: count URLs per adapter and per source_kind
uv run python -c "
import yaml, collections
y = yaml.safe_load(open('data/high-altitude-objects-2023/seed-urls.yaml'))
print('adapters:', collections.Counter(s['adapter'] for s in y['seeds']))
print('kinds:', collections.Counter(s['source_kind'] for s in y['seeds']))
"

# run the batch ingester
uv run signals ingest batch \
  --corpus "$CORPUS_VERSION" \
  --seeds data/high-altitude-objects-2023/seed-urls.yaml

# verify document count on Neon + Blob
uv run signals ingest status --corpus "$CORPUS_VERSION"
```

### Expected outputs

- The batch command prints a per-seed line with a green check or red cross, then a summary table with totals.
- On success the exit code is 0. On any partial failure the exit code is 1 and a failure list is printed; the command is designed to fail the run on any partial failure per `signals_ingest/cli.py:217-218`, which is intentional so the operator inspects failures rather than silently losing URLs.
- `signals ingest status --corpus $CORPUS_VERSION` should report a document count equal to the successful seed count.

### Acceptance criteria (from PHASED-PLAN.md Phase 4)

1. At least 90 documents successfully ingested.
2. At least five distinct source kinds represented.
3. Ingestion failure log captured at `research/YYYY-MM-DD-ingestion-run.md` with per-URL error codes and whether each failure was retried on the alternate adapter.
4. `signals ingest status` reports a document count matching the success count.

### Known failure modes

1. **Paywall blocks on tier-1 news.** NYT, WaPo, and Globe and Mail URLs are paywalled on the live web. The seed file routes all tier-1 news to `adapter: wayback`. If a Wayback snapshot does not exist for a given URL, the ingest will fail on that entry. Mitigation: re-run just that entry with `signals ingest direct --url ... --corpus $CORPUS_VERSION` and see whether the live URL is now accessible.
2. **FBI news-story 403.** The FBI news URL returned 403 under WebFetch during the research pass. The seed file routes this to `adapter: wayback`. If Wayback does not have a recent snapshot, the URL must be skipped or retrieved manually.
3. **war.gov redirects from defense.gov.** The DoD hosting rebrand of mid-2025 is preserved by 301/302 redirects on the old Article IDs. The seed file uses the current `war.gov` host. If the direct adapter does not follow redirects, some seeds may need manual re-routing.
4. **PRC MFA encoding.** The `fmprc.gov.cn` primary source may return content in encodings that trafilatura handles inconsistently. Expect manual intervention if the extraction produces garbled text.

## Phase 5 readiness

### Blocker: resolved

The `--narratives` CLI flag is now wired through `signals compute nvd`, `signals compute independence`, and `signals compute eval`. The constants module exposes two public functions:

- `find_narratives_yaml(topic: str = "nj-drones")` — walk-up resolver that locates `data/{topic}/narratives.yaml` from the module's installed location
- `load_narrative_defs(yaml_path)` — YAML loader returning the normalized list of narrative defs (slug, hypothesis, keywords, label, originating_source)

Module-level `NARRATIVE_DEFS` remains the nj-drones walk-up so existing invocations are unchanged. Omitting `--narratives` on a high-altitude-objects-2023 run will silently fall back to NJ drones definitions, so every Phase 5 run against this investigation must pass the flag. Test coverage at `python/signals_methods/tests/test_narratives_loader.py` includes a regression guard that the two corpora's slug sets differ.

### Secondary note: timeline loader

A similar hardcoded default exists for the timeline loader in the `eval` command at `signals_methods/cli.py:564,582`. Unlike narratives, `eval` already accepts `--timeline` as an override flag. Use the flag when running `signals compute eval`:

```
uv run signals compute eval \
  --corpus "$CORPUS_VERSION" \
  --topic high-altitude-objects-2023 \
  --timeline data/high-altitude-objects-2023/timeline.yaml
```

### Command sequence (once narratives loader is fixed)

```
cd /home/user/praxis-deng/dev/tell
export CORPUS_VERSION=high-altitude-objects-2023-YYYY-MM-DD

# IVI computation
uv run signals compute ivi \
  --corpus "$CORPUS_VERSION" \
  --topic high-altitude-objects-2023 \
  --window-days 7

# NVD computation (requires --narratives flag from preferred fix)
uv run signals compute nvd \
  --corpus "$CORPUS_VERSION" \
  --topic high-altitude-objects-2023 \
  --narratives data/high-altitude-objects-2023/narratives.yaml

# Source Independence Graph (same flag requirement)
uv run signals compute independence \
  --corpus "$CORPUS_VERSION" \
  --topic high-altitude-objects-2023 \
  --narratives data/high-altitude-objects-2023/narratives.yaml

# SQM evaluation (timeline flag already exists)
uv run signals compute eval \
  --corpus "$CORPUS_VERSION" \
  --topic high-altitude-objects-2023 \
  --timeline data/high-altitude-objects-2023/timeline.yaml
```

### Expected signal behavior (hypotheses for memo-writing)

These are the hypotheses the operator should look to confirm or contradict in the memos at `docs/methods/results/`:

1. **IVI.** Peak in the Feb 10-14 window, driven by the four shootdowns and the Montana radar anomaly occurring faster than the institutional-response cadence. Peak value should be comparable to or higher than the NJ drones Feb 24 2024 peak of 17.0 on a 7-day window.
2. **NVD.** High values for `hobbyist-pico-balloon` around Feb 17 (narrative velocity outpacing evidence accumulation as NIBBB announcement propagates). High values for `misidentification-threshold` around Feb 13 (narrative emerges in VanHerck briefing after the four engagements it explains). Strong negative divergence for `prc-surveillance` because evidence accumulation is unusually synchronous with narrative velocity (DoD attribution came first).
3. **SIG.** `prc-surveillance` should show many independent authoritative sources (war.gov, navy.mil, congress.gov, canada.ca, CSIS, CNA, tier-1 news). `official-recreation-research` should show one originating node (Kirby Feb 14 briefing) with downstream amplification but little independent corroboration. `hobbyist-pico-balloon` should show small but genuinely independent anchoring in NIBBB, WSPR communities, and tier-1 news reporting.
4. **SQM.** Contradicting-evidence lag for `prc-surveillance` is long (April NBC and December CNN reports contradict the DoD June 29 "did not collect" finding months after the fact). Contradicting-evidence lag for `official-recreation-research` is short and damning (the attribution preceded any evidence). Entropy floor across H1-H5 should stay above 50% of maximum across the window.

### Acceptance criteria (from PHASED-PLAN.md Phase 5)

1. Each memo reports specific numerical values, not qualitative assertions.
2. Each memo cites the exact timeline events that co-occur with signal peaks and troughs.
3. The cross-case synthesis explicitly states whether the Phase E claims in `dev/tell/docs/abstract-claims.md` strengthen, weaken, or stay unchanged with the second case added.
4. Writing-rules compliance throughout.

## Non-blockers that need noting

1. **defense.gov / war.gov redirect assumption.** This investigation assumes the direct adapter follows 301/302 redirects. If it does not, a one-line change to the adapter would be required. The NJ drones corpus used URLs that were all live at their original hosts, so this redirect-following behavior has not been exercised.
2. **Forum-adapter coverage.** The seed file contains one `forum` entry (NIBBB). The batch ingester routes it to the `direct` adapter. If the direct adapter does not produce useful extraction on a lightweight WordPress-style page, the entry should be re-routed to `wayback`.
3. **Single-entry source kinds.** `forum` (1) and `podcast` (1) are lightly represented. This is consistent with the underlying record: most podcast coverage was episodic and most forum content lives in paywalled or access-gated communities. For the SIG calculation, thin coverage in these categories is not a defect; it is the observation.

## Phase 4-5 total cost estimate

- Phase 4 ingestion: one working session (one to three hours for the run, plus up to a half-session for failure-log write-up and manual retries).
- Phase 5 code prerequisite: one working session for the proper `--narratives` flag fix, or fifteen minutes for the temporary file-swap path.
- Phase 5 signal runs: thirty minutes to one hour for all four computes against a ~100-document corpus.
- Phase 5 memo writing: one working session per memo, four memos, plus one working session for the cross-case synthesis. Five working sessions total.

Running all of Phase 4 and Phase 5 back to back is realistic in a single working week assuming the narratives-loader fix lands in a separate PR within that week.
