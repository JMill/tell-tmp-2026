/**
 * Drizzle schema for the OSINT weak signal detection pipeline.
 *
 * This is the canonical TypeScript/SQL schema. The Python side mirrors
 * these definitions in pydantic at
 * python/signals_core/src/signals_core/models.py.
 *
 * A schema-sync CI job regenerates Zod definitions from JSON Schema emitted
 * by the pydantic models and fails any PR where the result drifts.
 */
export * from "./sources";
export * from "./documents";
export * from "./corpus_versions";
export * from "./signal_ivi";
export * from "./signal_nvd";
export * from "./signal_independence";
export * from "./document_hypothesis_scores";
export * from "./hypothesis_distributions";
export * from "./controllers";
export * from "./advisories";
