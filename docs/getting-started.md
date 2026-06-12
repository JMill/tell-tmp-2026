# Getting Started

A walk-through of TELL as it actually works right now, after Stage 2 (Layer 0 ingestion + dashboard scaffold).

This is the single "how it works" document. Skip here when you want to understand the working system. For the design intent, see [`architecture.md`](architecture.md). For the novel methods (IVI, NVD, Source Independence Graph, SQM), see [`methods/`](methods/).

## What works today

As of 2026-04-08, the pipeline has a working end-to-end vertical slice:

```
archive.org Wayback Machine
  └─ signals_ingest (Python)
       ├─ CDX API snapshot resolution
       ├─ HTML fetch with id_ modifier (strips Wayback toolbar)
       ├─ trafilatura text extraction
       ├─ SHA-256 content hash
       ├─ Vercel Blob upload (raw HTML, private)
       └─ Neon Postgres insert (metadata + source row)

Neon Postgres
  └─ @tells-fyi/db (Drizzle)
       └─ Next.js 16 dashboard (apps/dashboard)
            ├─ Server Component queries via Drizzle
            ├─ Suspense streaming of corpus summary and recent documents
            └─ Tailwind v4 with editorial palette tokens
```

One document has been ingested as the smoke test (the Wikipedia article on the 2024 US drone sightings). The dashboard renders that document's metadata live.

Everything else from the approved plan (Layer 1 classification, Layer 2 weak signal methods, Layer 3 sensemaking interface, Layer 4 evaluation) is stub-only at this stage.

## Prerequisites

Before running anything, you need these installed on your machine:

- **Node.js 22+** (Next.js 16 and pnpm 10 require it)
- **pnpm 10.12+** — installed automatically via corepack if you have a `packageManager` field in `package.json`
- **Python 3.12+**
- **uv** — the Python workspace manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Vercel CLI** — for pulling environment variables (`pnpm add -g vercel@latest`)
- **A linked Vercel project** with Neon Postgres and a Vercel Blob store connected

The Vercel project for this repo is `wfs/tell-fyi`. The linked resources are `neon-gray-mirror` (Neon Postgres) and Vercel Blob (private).

## First-time setup

Run these once from `dev/tell/`:

```bash
# Pull Vercel environment variables (DATABASE_URL, BLOB_READ_WRITE_TOKEN, etc.)
vercel env pull .env.local --yes

# Install Node workspace dependencies (@tells-fyi/db, dashboard)
pnpm install

# Install Python workspace dependencies (signals_core, signals_ingest, signals_cli)
uv sync

# Push the Drizzle schema to Neon (creates sources, documents, corpus_versions tables)
pnpm --filter @tells-fyi/db exec drizzle-kit push --force
```

The dashboard also needs `.env.local` available at its root. Symlinked:

```bash
ln -sf ../../.env.local apps/dashboard/.env.local
```

This symlink is already in place in the working tree.

## Ingesting a document

From `dev/tell/`, run the CLI:

```bash
uv run signals ingest wayback \
  --url "https://en.wikipedia.org/wiki/2024_United_States_drone_sightings" \
  --corpus "nj-drones-2026-04-07"
```

What happens:

1. **Resolve snapshot.** The adapter queries the [Wayback CDX API](https://web.archive.org/cdx/search/cdx) for snapshots of the URL, filtered to `statuscode:200`, and picks the most recent.
2. **Fetch raw HTML.** GET against `https://web.archive.org/web/{timestamp}id_/{original_url}`. The `id_` modifier strips Wayback's navigation toolbar so the HTML is pristine.
3. **Extract.** `trafilatura` pulls the readable text plus metadata (title, author, published date, language).
4. **Upload raw HTML to Vercel Blob.** PUT to `https://vercel.com/api/blob/?pathname=corpus/{version}/{domain}/{sha256}.html` with the required headers (`x-vercel-blob-access: private`, `x-api-version: 12`, etc.). This endpoint pattern was reverse-engineered from `@vercel/blob/dist/chunk-*.js` and is **not publicly documented**.
5. **Upsert the source.** Insert a row in `sources` if the domain is new, or return the existing id.
6. **Insert the document.** Write a row to `documents` with the source id, URL, content hash, Blob key, and any extracted metadata. The `content_hash` column has a unique index, so re-running the same URL is idempotent.

On success, you see a Rich table with the document id, blob URL, and extracted character count.

Check the corpus status:

```bash
uv run signals ingest status --corpus nj-drones-2026-04-07
```

## Running the dashboard

From `dev/tell/`:

```bash
pnpm --filter dashboard dev
```

This starts Next.js with Turbopack on `http://localhost:3000` (or the next free port). The dashboard:

- Queries Neon via Drizzle in Server Components
- Streams the corpus summary (document count, source count, latest title) and recent documents list via React Suspense
- Uses a placeholder editorial palette (off-white `#F6F4EE` background, near-black `#111714` text, muted accent). These are not the final tokens; they are there to exercise the layout.

To run a production build locally:

```bash
pnpm --filter dashboard build
pnpm --filter dashboard start
```

## The data model

See `packages/db/src/schema/` for the canonical TypeScript definitions and `python/signals_core/src/signals_core/models.py` for the pydantic mirrors.

| Table | Purpose | Key columns |
|---|---|---|
| `sources` | Where documents originate | `id` (ULID), `domain`, `name`, `kind` (enum), `reliability_score`, `first_seen_at` |
| `documents` | Individual fetched documents | `id`, `source_id` (FK), `url`, `content_blob_key`, `content_hash` (unique), `metadata` (jsonb), `corpus_version` |
| `corpus_versions` | Frozen corpus snapshots for reproducibility | `id`, `label`, `document_count`, `commit_sha` |

**Not yet implemented** (stubs or empty):
- `document_embeddings` (pgvector) — Layer 1
- `document_hypothesis_scores` — Layer 1
- `hypothesis_distributions` — Layer 1
- `narratives`, `narrative_documents` — Layer 1
- `signal_ivi`, `signal_nvd`, `signal_independence`, `signal_sqm` — Layer 2
- `evaluation_runs` — Layer 4

These will land as the subsequent layers ship. The schema additions should go through `drizzle-kit generate` for migrations so Neon stays in a known state.

## Repository layout

```
dev/tell/
├── apps/
│   └── dashboard/              # Next.js 16 App Router dashboard
│       ├── app/
│       │   ├── page.tsx        # Home: corpus summary + recent documents
│       │   ├── layout.tsx      # Root layout with Geist fonts + editorial palette
│       │   └── _components/    # Server Components (corpus-summary, document-list)
│       ├── lib/queries.ts      # Server-only Drizzle queries
│       └── package.json
├── packages/
│   └── db/                     # @tells-fyi/db — Drizzle schema + Neon client
│       ├── src/
│       │   ├── client.ts       # db instance from @neondatabase/serverless
│       │   ├── schema/         # Table definitions per file
│       │   └── index.ts
│       └── drizzle.config.ts
├── python/
│   ├── signals_core/           # pydantic source of truth
│   ├── signals_ingest/         # adapters, extract, storage
│   │   └── src/signals_ingest/adapters/wayback.py
│   └── signals_cli/            # Typer CLI (`signals ...`)
├── data/
│   ├── hypotheses.yaml         # H1-H5 CU26 framework
│   └── nj-drones/
│       ├── timeline.yaml       # Hand-curated ground truth (JMill-authored, stub)
│       ├── narratives.yaml     # Narrative definitions
│       ├── seed-urls.yaml      # Seed URLs for ingestion (stub)
│       └── research/           # Verified + unverified research dossiers
├── docs/
│   ├── architecture.md         # Design intent (from the plan)
│   ├── getting-started.md      # This file
│   └── methods/                # Paper-ready method documentation stubs
├── corpus/                     # Raw fetched documents (gitignored)
├── pyproject.toml              # uv workspace root
├── package.json                # pnpm workspace root
├── pnpm-workspace.yaml
├── .env.local                  # Vercel env (gitignored)
├── .vercel/                    # Vercel project link (gitignored)
└── CLAUDE.md                   # Subtree conventions
```

## Quirks and gotchas (documented so they don't bite twice)

These are real issues we hit during Stage 2. Fixes are already in the code.

1. **Wayback availability API is flaky over httpx.** `https://archive.org/wayback/available` returns empty `archived_snapshots` intermittently. Use the CDX API (`https://web.archive.org/cdx/search/cdx`) instead. Also requires `Accept: */*` header explicitly — httpx's default headers cause empty responses.

2. **Vercel Blob REST endpoint is NOT `blob.vercel-storage.com`.** That's where blob URLs resolve, not where uploads go. The actual upload endpoint is `https://vercel.com/api/blob/?pathname={pathname}` with headers `x-vercel-blob-access`, `x-api-version: 12`, `x-content-type`, `x-add-random-suffix`. Reverse-engineered from the `@vercel/blob` JS SDK source at `node_modules/@vercel/blob/dist/chunk-*.js`. See `python/signals_ingest/src/signals_ingest/storage.py`.

3. **Turbopack rejects `.js` extension imports on `.ts` source files.** TypeScript's bundler module resolution allows `import './foo.js'` for a `foo.ts` file, but Turbopack does not. Omit extensions entirely in cross-package imports. See `packages/db/src/schema/index.ts`.

4. **Dashboard needs `drizzle-orm` and `@neondatabase/serverless` as direct dependencies**, not just transitively through `@tells-fyi/db`. TypeScript's module resolution needs them local to the dashboard for type resolution.

5. **uv workspace members must be declared as dependencies of the root `pyproject.toml`** in addition to being listed under `[tool.uv.workspace]`. Without it, `uv sync` installs only dev-dependencies and none of the workspace packages.

6. **`drizzle-kit push` is interactive by default.** Set `strict: false` in `drizzle.config.ts` and run with `--force` to push non-interactively.

7. **Blob stores need explicit project connection** and the CLI prompt for this is not scriptable. The undocumented REST endpoint `DELETE /v1/storage/stores/blob/{storeId}` works via `vercel api`. Creation-with-connection currently requires a dashboard click.

8. **`.env.local` at the pipeline root is symlinked from `apps/dashboard/.env.local`** because Next.js loads from the app root, not the monorepo root. If you re-pull env vars, they propagate through the symlink automatically.

## Verifying the pipeline still works (smoke test)

After any non-trivial change to the ingestion stack, schema, or dashboard, run:

```bash
bash scripts/smoke-test.sh
```

This runs, in order:

1. Environment sanity check (`.env.local` exists)
2. Python CLI reachable (`uv run signals --help`)
3. Python unit tests (`pytest` on `signals_core` and `signals_ingest`)
4. TypeScript typecheck on `@tells-fyi/db` and the dashboard
5. Neon connectivity via `signals ingest status`
6. End-to-end ingest of a known URL via Wayback (one document into Neon + Blob)
7. Corpus count verification
8. Next.js production build

All checks run in under a minute. If any step fails, the script stops with a clear error. The Quirks section above covers most known failure modes.

Override the test corpus and URL with environment variables if you want to smoke-test against different data without polluting a real corpus:

```bash
SMOKE_TEST_CORPUS=my-smoke-2026-04-08 \
SMOKE_TEST_URL=https://example.com/test \
  bash scripts/smoke-test.sh
```

## What's next

See [`NEXT-STEPS.md`](NEXT-STEPS.md) for the current phase and the full confidence plan. The short version: the pipeline technically runs but none of the abstract's scientific claims are empirically validated yet. Priority is **Phase A: build a real NJ drones corpus**, then **Phase B: implement and validate IVI**, then the remaining claims. See [`abstract-claims.md`](abstract-claims.md) for the claim-by-claim status.

See [`plan.md`](plan.md) for the full approved implementation plan and [`architecture.md`](architecture.md) for the design intent.
