# signals_analyze

LLM-driven analysis layer for the OSINT pipeline. The first contribution is **H1-H5 hypothesis scoring** — for each document in a corpus, ask Claude to estimate the probability that the document supports each of the five CU26 hypotheses, with a brief rationale.

## Methods

| Method | File | Status |
|---|---|---|
| **H1-H5 hypothesis scoring** | `src/signals_analyze/hypothesis_scoring.py` | Phase C (2026-04-08) |
| Source reliability scoring (SAT framework) | planned | Phase C+ |
| Embeddings via AI Gateway | planned | Phase C+ |

## Design principles

1. **Idempotent at the (document, prompt_version, model) level.** Re-running the scorer with the same prompt and model overwrites prior rows for the same document via the unique constraint on `document_hypothesis_scores`. Bumping the prompt version produces a new row so the prior version stays auditable.

2. **Tool-use for structured output.** The Anthropic SDK's tool calling guarantees JSON conformant to a schema. We define a `record_hypothesis_scores` tool with H1-H5 fields and force the model to invoke it. No regex, no JSON repair, no `json.loads(text)` failures.

3. **Content fetched on demand.** Document text is not cached in Postgres. The scorer fetches the raw HTML from Vercel Blob using the `BLOB_READ_WRITE_TOKEN` and re-extracts with trafilatura at scoring time. This adds ~50ms per document but keeps the schema simple. Move to a cached extracted-text column if cost becomes a concern.

4. **Cost transparency.** The CLI prints token usage and estimated cost after each batch run. For the NJ drones corpus (38 documents) with Haiku 4.5, expected cost is well under $0.10.

## Usage

```bash
# Score the entire corpus
uv run signals analyze hypotheses --corpus nj-drones-2026-04-08 --topic nj-drones

# Pilot run on the first 5 documents to validate prompt + parsing
uv run signals analyze hypotheses --corpus nj-drones-2026-04-08 --topic nj-drones --pilot 5

# Show what's been scored
uv run signals analyze hypotheses-status --corpus nj-drones-2026-04-08
```
