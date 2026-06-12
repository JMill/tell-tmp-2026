# signals_ingest

Source adapters for fetching documents from open sources and writing them to Neon Postgres + Vercel Blob.

## Architecture

Each adapter follows the same interface: given a list of seed URLs or a query, it yields `Document` instances with `source_id`, `url`, `fetched_at`, `content_hash`, and metadata populated. The shared pipeline code handles:

1. Content extraction (via `trafilatura`)
2. Blob upload of the raw payload
3. Neon insert of the structured metadata

Adapters are stateless and resumable. They write a checkpoint after each successful ingest so a interrupted run can resume without re-fetching.

## Adapters (Stage 2)

- **wayback** — `adapters/wayback.py`. Fetches archived snapshots from web.archive.org. First adapter.
- **reddit** — TBD
- **congressional** — TBD
- **aaro** — TBD
- **arxiv** — TBD

## CLI

```bash
uv run signals ingest wayback --url https://www.nytimes.com/2024/12/12/us/new-jersey-drone-sightings.html
```
