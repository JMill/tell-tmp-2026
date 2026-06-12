/**
 * Corpus versions — frozen snapshots for reproducibility.
 *
 * Each batch run produces a corpus version with a stable label. Demos are
 * pinned to a specific version (via Neon database branches). Evaluation runs
 * reference a version so results are reproducible.
 */
import { integer, pgTable, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const corpusVersions = pgTable(
  "corpus_versions",
  {
    id: text("id").primaryKey(), // ULID
    label: text("label").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    manifestBlobKey: text("manifest_blob_key"),
    documentCount: integer("document_count").notNull().default(0),
    commitSha: text("commit_sha"),
  },
  (table) => ({
    labelIdx: uniqueIndex("corpus_versions_label_idx").on(table.label),
  }),
);

export type CorpusVersion = typeof corpusVersions.$inferSelect;
export type NewCorpusVersion = typeof corpusVersions.$inferInsert;
