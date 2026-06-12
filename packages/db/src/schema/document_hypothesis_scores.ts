/**
 * Document hypothesis scores — per-document H1-H5 probabilities.
 *
 * One row per (document_id, hypothesis_id, prompt_version, model) tuple.
 * Re-running the scorer with the same prompt version and model overwrites
 * via the unique constraint. Bumping the prompt version produces a new
 * row so old scores remain auditable.
 *
 * Mirrors signals_core.DocumentHypothesisScore in
 * python/signals_core/src/signals_core/models.py.
 */
import { index, pgTable, real, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

import { documents } from "./documents";

export const documentHypothesisScores = pgTable(
  "document_hypothesis_scores",
  {
    id: text("id").primaryKey(), // ULID
    documentId: text("document_id")
      .notNull()
      .references(() => documents.id, { onDelete: "cascade" }),
    hypothesisId: text("hypothesis_id").notNull(), // H1, H2, H3, H4, H5
    score: real("score").notNull(),
    rationale: text("rationale"),
    model: text("model").notNull(), // e.g. claude-haiku-4-5-20251001
    promptVersion: text("prompt_version").notNull(), // e.g. h15-v1
    scoredAt: timestamp("scored_at", { withTimezone: true }).notNull(),
  },
  (table) => ({
    docHypothesisIdx: uniqueIndex("dhs_doc_hyp_prompt_model_idx").on(
      table.documentId,
      table.hypothesisId,
      table.promptVersion,
      table.model,
    ),
    documentIdIdx: index("dhs_document_id_idx").on(table.documentId),
    hypothesisIdIdx: index("dhs_hypothesis_id_idx").on(table.hypothesisId),
  }),
);

export type DocumentHypothesisScoreRow = typeof documentHypothesisScores.$inferSelect;
export type NewDocumentHypothesisScoreRow = typeof documentHypothesisScores.$inferInsert;
