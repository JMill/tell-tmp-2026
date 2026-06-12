# TELL

**Totally Explainable, Looks Legit.** A weak-signal detection pipeline for information environments where the comfortable explanation is usually wrong.

In poker, a "tell" is the unconscious signal that reveals what someone is concealing. In storytelling, to "tell" is to narrate. The pipeline detects tells (weak signals) hiding inside tells (narratives).

> **Time capsule.** This repository is a frozen snapshot of the TELL pipeline exactly as presented at the Carnegie Mellon Technology, Management, and Policy Graduate Consortium on June 16, 2026, under the title *Sensemaking quality, not prediction: three measures for detecting narrative capture*. It is archived and will not change. Development continues; future milestones will be published the same way. The live dashboard is at [tell-fyi.vercel.app](https://tell-fyi.vercel.app), the talk slides at [tell-fyi.vercel.app/tmp26](https://tell-fyi.vercel.app/tmp26), and the deck plus its figure build pipeline are in [`talk/`](talk/).

## What this is

An engineering instantiation of JMill's praxis. The pipeline applies structured analytical techniques to discourse around ambiguous, high-uncertainty events. It does not predict truth. It structures how human-machine teams evaluate competing explanations.

The first validation case study is the November 2024 - January 2025 New Jersey aerial phenomena incident. The pipeline is built to generalize beyond that case to any policy domain where institutions must manage discourse around uncertain events (biosecurity, emerging technology, critical infrastructure, algorithmic amplification).

## Novel contributions

Three data-driven methods introduced by this work:

- **Information Vacuum Index (IVI)** — quantifies the gap between public discourse volume and authoritative institutional response
- **Narrative Velocity Divergence (NVD)** — flags when narratives accelerate faster than supporting evidence accumulates
- **Source Independence Graph** — distinguishes genuine multi-source corroboration from echo amplification

Plus a fourth evaluation contribution:

- **Sensemaking Quality Metrics (SQM)** — evaluates sensemaking *process* rather than prediction accuracy. Grounded in Klein's sensemaking framework.

All four are implemented in the Python package `signals_methods/` and documented for paper citation in [`docs/methods/`](docs/methods/).

## Architecture at a glance

Hybrid monorepo:

- **Python** (`python/`) owns the analysis pipeline. Ingestion, embeddings, Bayesian H1-H5 hypothesis evaluation, the novel signal methods, retrospective evaluation. Runs offline on laptop and CI.
- **TypeScript/Next.js** (`packages/`, `apps/dashboard/`) owns the interactive dashboard. Deploys to Vercel. Reads precomputed results from Neon Postgres and raw documents from Vercel Blob.
- **Shared schemas** (`schemas/`) keep pydantic and zod type definitions in sync via CI.

See [`docs/architecture.md`](docs/architecture.md) for the full design.

## Tooling

- **Python:** `uv` workspaces, `pydantic` v2, `pytest`, `typer` CLI
- **TypeScript:** `pnpm` workspaces, Next.js 16 App Router, Drizzle ORM, AI SDK v6
- **Visualization:** Visx (custom charts), React Flow (Source Independence Graph), shadcn/ui + Tailwind v4
- **Data:** Neon Postgres with pgvector (via Vercel Marketplace) + Vercel Blob
- **LLM orchestration:** AI SDK v6 + Vercel AI Gateway (interactive); anthropic Python SDK (batch)

## Documentation map

| Doc | When to read it |
|---|---|
| [`docs/getting-started.md`](docs/getting-started.md) | First. How the system actually works today, setup, day-to-day workflow, 7 debugging quirks. |
| [`docs/NEXT-STEPS.md`](docs/NEXT-STEPS.md) | Next. Current phase, confidence plan, what to pick up. |
| [`docs/abstract-claims.md`](docs/abstract-claims.md) | When you're asking "is this defensible for CMU?" Tracks every abstract claim to its empirical status. |
| [`docs/plan.md`](docs/plan.md) | Full approved implementation plan. Stage gates, risks, mitigations. |
| [`docs/architecture.md`](docs/architecture.md) | Design intent. Written before Stage 2 landed; may have drift. |
| [`docs/methods/{ivi,nvd,independence,sqm}.md`](docs/methods/) | Paper-ready method definitions for citation. |
| [`CLAUDE.md`](CLAUDE.md) | Subtree conventions: language tooling, aesthetic, testing, secrets, do-not list. |

## Quick start

Full walk-through in [`docs/getting-started.md`](docs/getting-started.md). Short version:

```bash
# One-time setup (from dev/tell/)
vercel env pull .env.local --yes
pnpm install
uv sync
pnpm --filter @tells-fyi/db exec drizzle-kit push --force

# Ingest a document via the Wayback Machine
uv run signals ingest wayback \
  --url "https://en.wikipedia.org/wiki/2024_United_States_drone_sightings" \
  --corpus "nj-drones-2026-04-07"

# Check corpus status
uv run signals ingest status --corpus nj-drones-2026-04-07

# Run the dashboard
pnpm --filter dashboard dev

# Verify everything still works after changes
bash scripts/smoke-test.sh
```

## Repository layout

```
tell/
├── packages/                   # TypeScript packages
│   ├── core/                   # shared zod schemas
│   ├── db/                     # Drizzle schema + queries
│   ├── blob/                   # Vercel Blob helpers
│   ├── ai/                     # AI SDK v6 config, tools, prompts
│   ├── charts/                 # Visx chart components
│   ├── graph/                  # React Flow Source Independence Graph
│   └── ui/                     # shadcn primitives + design tokens
├── python/                     # Python packages (uv workspace members)
│   ├── signals_core/           # pydantic models
│   ├── signals_ingest/         # source adapters
│   ├── signals_analyze/        # embeddings, topics, classification
│   ├── signals_methods/        # IVI/NVD/Independence/SQM (extractable)
│   ├── signals_export/         # Neon + Blob writers
│   ├── signals_eval/           # retrospective evaluation
│   └── signals_cli/            # Typer CLI aggregator
├── apps/
│   └── dashboard/              # Next.js App Router app
├── schemas/                    # JSON Schema bridge (pydantic → zod)
├── data/
│   └── nj-drones/              # ground-truth timeline and seed URLs
├── corpus/                     # gitignored; raw fetched documents
├── docs/
│   ├── architecture.md         # full design document
│   └── methods/                # paper-ready method docs
└── scripts/
```

## Related work

- **Praxis paper:** `../../paper/` (forthcoming)
- **The Uncertainty Game:** `../../artifact/` (sibling artifact; shares the same underlying architecture)
- **CU26 collaborative paper:** source material in `../../intake/` pending publication
- **Lawfare policy piece:** "The Disclosure Trap" in `../../intake/` pending publication
- **First engagement using this work:** `../../engagements/2026-tmp-cmu/`

## What is included, and what is not

This snapshot carries the full analysis code, the dashboard, the method documentation, the empirical claim ledger ([`docs/abstract-claims.md`](docs/abstract-claims.md)), the hand-audited ground-truth timeline ([`data/nj-drones/timeline.yaml`](data/nj-drones/timeline.yaml)), the talk deck, and the figure build pipeline with its extracted data series. The document corpus itself is not redistributed: source documents remain under their publishers' copyright, and the database and blob store the pipeline reads from are not bundled. The seed URL lists and ingestion code reconstruct the corpus; the claim ledger and the figure data record what the analysis found.

## Citation

Miller, Jonathan. "Sensemaking quality, not prediction: three measures for detecting narrative capture." CMU Technology, Management, and Policy Graduate Consortium, Pittsburgh, June 16, 2026. Pipeline snapshot: https://github.com/JMill/tell-tmp-2026

A `CITATION.cff` file is included for reference managers.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Contact

Jonathan "JMill" Miller · jbm213@psu.edu · [linkedin.com/in/jmill](https://www.linkedin.com/in/jmill/)
Doctor of Engineering Program, School of Engineering Design and Innovation, The Pennsylvania State University
