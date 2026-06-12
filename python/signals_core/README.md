# signals_core

Shared pydantic v2 data models for the OSINT weak signal detection pipeline. Source of truth for cross-language schemas.

The TypeScript side mirrors these models in Zod (`packages/core/src/schemas/`). A CI job regenerates Zod from these pydantic models and fails if the result drifts.

Packages that depend on this one:
- `signals_ingest`
- `signals_analyze`
- `signals_methods`
- `signals_export`
- `signals_eval`
- `signals_cli`
