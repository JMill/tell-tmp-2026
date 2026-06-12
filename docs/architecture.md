# Architecture — TELL Weak-Signal Detection Pipeline

This document is the technical architecture for `dev/tell/`. It captures the design decisions, the package boundaries, and the rationale for each major choice.

The plan that produced this architecture is at `/Users/jmill/.claude/plans/frolicking-swinging-map.md`.

## Purpose

The pipeline applies structured analytical techniques to discourse around ambiguous, high-uncertainty events. Unlike prediction-oriented OSINT tools, it evaluates *sensemaking quality* rather than prediction accuracy. The first validation case study is the November 2024 - January 2025 New Jersey aerial phenomena incident.

## Substantive contributions

The pipeline introduces four novel methods, all implemented in the Python `signals_methods/` package:

1. **Information Vacuum Index (IVI)** — quantifies the gap between public discourse volume and authoritative institutional response on a topic. High IVI signals an information environment vulnerable to narrative capture.

2. **Narrative Velocity Divergence (NVD)** — flags when narratives accelerate faster than supporting evidence accumulates. Targets speculative drift.

3. **Source Independence Graph** — distinguishes genuine multi-source corroboration from echo amplification by tracing citation chains and information flow between sources.

4. **Sensemaking Quality Metrics (SQM)** — evaluates the human-machine team's sensemaking *process* against a hand-curated ground-truth timeline. Includes hypothesis coverage, evidence-narrative alignment, update responsiveness, and premature closure resistance. Grounded in Klein's sensemaking framework.

## Design principles

- **Sensemaking-native, not prediction-native.** The pipeline does not output a guess about what an ambiguous phenomenon "is." It outputs structured evidence, hypothesis distributions, and weak signal alerts that support human evaluation.
- **Klein's sensemaking activities are design requirements.** The interactive interface is organized around Klein's six activities (Elaborating, Questioning, Connecting, Comparing, Framing, Re-Framing).
- **Bayesian hypothesis updating preserves uncertainty.** The CU26 H1-H5 framework is the substrate. Hypothesis distributions update with each new piece of evidence; the system never collapses to a single answer prematurely.
- **Source-aware structured analysis.** Source reliability is evaluated using the SAT (Structured Analytical Technique) framework from the Lawfare piece. Provenance, track record, independence, and specificity all factor into reliability scores.
- **Reproducibility by design.** Every retrospective run is keyed to a stable corpus version. Neon database branches, parquet checkpoints, and YAML manifests make any past result replayable.

## Architecture overview

Hybrid Python + TypeScript monorepo. Python handles the offline analysis pipeline. TypeScript handles the interactive dashboard deployed to Vercel.

### Why hybrid

Python has the mature library ecosystem for NLP, graph analytics (networkx), Bayesian computation, and scientific computing. TypeScript on Vercel gives the dashboard the best deployment story, the best interactive agent tooling (AI SDK v6), and the design control needed for the editorial-journal aesthetic. Splitting the work between the two languages matches each layer to its strongest ecosystem.

The Python `signals_methods/` package is designed to be independently extractable and citable as a standalone research artifact.

### Division of labor

| Concern | Owner |
|---|---|
| Source ingestion adapters (Wayback, Reddit, Congressional, AARO, arXiv, ASRS) | Python (`signals_ingest`) |
| Document extraction and dedup | Python (`signals_ingest`) |
| Embedding generation | Python (`signals_analyze`) |
| Topic clustering | Python (`signals_analyze`) |
| Source reliability scoring (SAT framework) | Python (`signals_analyze`) via batched LLM calls |
| Hypothesis-evidence mapping (H1-H5) | Python (`signals_analyze`) via batched LLM calls |
| The four novel methods (IVI, NVD, Source Independence Graph, SQM) | Python (`signals_methods`) |
| Database writes | Python (`signals_export`) |
| Retrospective evaluation | Python (`signals_eval`) |
| Dashboard UI | TypeScript (`apps/dashboard`) |
| Interactive sensemaking agent | TypeScript (`packages/ai`) via AI SDK v6 |
| Charts and visualizations | TypeScript (`packages/charts`, `packages/graph`) |

## Package boundaries

### TypeScript packages (`packages/`)

| Package | Purpose | Key dependencies |
|---|---|---|
| `core` | Shared zod schemas (mirrored from pydantic), constants | `zod` |
| `db` | Drizzle schema and query helpers | `drizzle-orm`, `@neondatabase/serverless` |
| `blob` | Vercel Blob read helpers | `@vercel/blob` |
| `ai` | AI SDK v6 config, tool definitions, sensemaking agent | `ai`, `@ai-sdk/anthropic`, `@ai-sdk/openai` |
| `charts` | Visx chart components (time series, IVI gauge, NVD divergence, hypothesis distribution) | `@visx/*`, `d3` |
| `graph` | React Flow Source Independence Graph component | `@xyflow/react`, `elkjs` |
| `ui` | shadcn/ui primitives + design tokens | `@radix-ui/*`, `tailwind`, `framer-motion` |

### Python packages (`python/`)

| Package | Purpose | Key dependencies |
|---|---|---|
| `signals_core` | Pydantic v2 source-of-truth data models | `pydantic` |
| `signals_ingest` | Source-specific ingestion adapters | `httpx`, `trafilatura`, `pypdf` |
| `signals_analyze` | Embeddings, topics, classification | `sentence-transformers`, `scikit-learn`, `instructor`, `anthropic` |
| `signals_methods` | The four novel methods (extractable research package) | `numpy`, `scipy`, `networkx`, `pandas` |
| `signals_export` | Neon Postgres and Vercel Blob writers | `psycopg`, `httpx` |
| `signals_eval` | Retrospective evaluation against ground truth | `signals_core`, `signals_methods` |
| `signals_cli` | Top-level Typer CLI aggregating the rest | `typer` |

### Cross-language schema sync

`python/signals_core/src/signals_core/models.py` is the source of truth. A CI job emits JSON Schema from the pydantic models, then generates zod definitions in `packages/core/src/schemas/generated/`. A second CI job (`schemas-in-sync`) fails any PR where the generated TypeScript drifts from what should be produced by the current pydantic models.

Manual TS-only schemas live in `packages/core/src/schemas/manual/` and are not regenerated.

## Data architecture

### Storage layer

- **Neon Postgres** (provisioned via Vercel Marketplace) for all structured data. Includes pgvector for embeddings. Database branching enables snapshotting "the corpus as of date X" and pinning the demo to a frozen branch.
- **Vercel Blob** for all raw document payloads. Keyed by `corpus/{version}/{source}/{sha256}.{ext}`.

### Schema sketch

Tables (Drizzle, mirrored in Pydantic):

- `documents` — id, source_id, url, fetched_at, published_at, title, content_blob_key, content_hash, metadata (jsonb), corpus_version
- `document_embeddings` — document_id, embedding (vector(1536)), model
- `sources` — id, domain, name, kind, reliability_score, reliability_factors (jsonb)
- `citations` — from_document_id, to_document_id OR to_source_url, kind
- `hypotheses` — id (H1-H5), label, definition, prior
- `document_hypothesis_scores` — document_id, hypothesis_id, score, rationale, model
- `hypothesis_distributions` — topic_id, timestamp, distribution (jsonb), entropy, mode
- `narratives` — id, label, seed_document_id, embedding (vector)
- `narrative_documents` — narrative_id, document_id, confidence
- `signal_ivi` — topic_id, window_start, window_end, value, components (jsonb)
- `signal_nvd` — narrative_id, window_start, window_end, narrative_velocity, evidence_velocity, value
- `signal_independence` — topic_id, timestamp, independence_score, node_count, edge_count, graph_blob_key
- `signal_sqm` — evaluation_run_id, timestamp, hypothesis_coverage, evidence_alignment, update_responsiveness, premature_closure_resistance, composite
- `corpus_versions` — id, label, created_at, manifest_blob_key, document_count, commit_sha
- `evaluation_runs` — id, corpus_version_id, method_version, config (jsonb), created_at

### Reproducibility

Every batch run produces a corpus version with a stable label like `nj-drones-2026-05-15`. The manifest YAML pins ingestion adapter versions, query parameters, document count, date ranges, tool versions, and random seeds. Manifests are committed to git at `data/nj-drones/manifests/{version}.yaml`. Neon branches are cut per corpus version. Parquet checkpoints under `corpus/{version}/parquet/` enable local re-runs without re-fetching.

## Visualization conventions

Editorial-journal aesthetic, not generic AI template. See `CLAUDE.md` in this directory for the full visual conventions.

- **Visx** for all hero charts (time series, NVD divergence, IVI gauge, hypothesis distribution)
- **React Flow + ELK** for the Source Independence Graph
- **shadcn/ui + Tailwind v4** with custom tokens for primitives
- **Framer Motion** for transitions only, never continuous animation

## Deployment

- **Dashboard**: Vercel project linked to `apps/dashboard/`. Standard Next.js deployment.
- **Database**: Neon Postgres via Vercel Marketplace, env vars auto-bound.
- **Blob**: Vercel Blob, env vars auto-bound.
- **Python**: runs offline on JMill's laptop and in CI for the TMP demo. No Python on Vercel for June 15. Any live ingestion story is post-June.
- **Demo pinning**: a frozen Neon branch (e.g. `tmp-cmu-frozen-2026-06-08`) backs the demo dashboard so nothing changes under the presenter.

## Build sequence

Stages are sequential and gated by completion criteria. The full sequence with gates is in `/Users/jmill/.claude/plans/frolicking-swinging-map.md`. Summary:

- Stage 0: Scaffolding + ground-truth timeline authoring
- Stage 1: Abstract submission to CMU (April 23)
- Stage 2: Layer 0 — Ingestion + dashboard scaffold
- Stage 3: Layer 1 — Classification + design tokens
- Stage 4: Layer 2 — Weak signal methods (IVI, NVD, Independence)
- Stage 5: Layer 3 — Sensemaking interface
- Stage 6: Layer 4 — Evaluation + method docs
- Stage 7: Polish + talk prep
- Stage 8: Delivery (June 15-16)

## Risks

- **Ground-truth timeline quality** is the load-bearing dependency. JMill personally authors. Two-pass refinement.
- **Retrospective data availability** for late 2024 social media is uneven. Lean on Wayback and GDELT for news. Accept imperfect social coverage as a paper limitation.
- **LLM cost overrun** beyond $50-200. Aggressive hash-based caching at `(document_hash, prompt_hash)` level. Pilot runs before full runs.
- **Two-language schema drift**. Automated CI sync from day one.
- **Aesthetic fails to land**. Design tokens are a hard gate for Stage 3. Not deferred to Stage 7.
- **Python deployment ambiguity**. Firm commitment: offline only for the TMP demo.
