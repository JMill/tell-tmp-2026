# signals_cli

Top-level Typer CLI that aggregates subcommands from the other Python packages.

Usage:

```bash
uv run signals --help
uv run signals ingest --help
uv run signals ingest wayback --url https://example.com
```

Subcommands:
- `ingest` — fetch documents from source adapters (`signals_ingest`)
- `analyze` — embeddings, source reliability, hypothesis scoring (`signals_analyze`, later)
- `compute` — run signal methods (IVI, NVD, Independence Graph) (`signals_methods`, later)
- `eval` — retrospective evaluation against ground truth (`signals_eval`, later)
- `export` — write results to Neon/Blob (`signals_export`, later)
