/**
 * Document table — a single fetched document.
 *
 * Raw content lives in Vercel Blob (keyed by contentBlobKey).
 * Structured metadata lives here.
 *
 * Mirrors the pydantic Document model in
 * python/signals_core/src/signals_core/models.py
 */
import { relations } from "drizzle-orm";
import { index, jsonb, pgTable, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

import { sources } from "./sources";

export const documents = pgTable(
  "documents",
  {
    id: text("id").primaryKey(), // ULID
    sourceId: text("source_id")
      .notNull()
      .references(() => sources.id, { onDelete: "restrict" }),
    url: text("url").notNull(),
    canonicalUrl: text("canonical_url"),
    fetchedAt: timestamp("fetched_at", { withTimezone: true }).notNull(),
    publishedAt: timestamp("published_at", { withTimezone: true }),
    title: text("title"),
    contentBlobKey: text("content_blob_key"),
    extractedTextBlobKey: text("extracted_text_blob_key"),
    contentHash: text("content_hash").notNull(),
    metadata: jsonb("metadata").$type<Record<string, unknown>>().notNull().default({}),
    corpusVersion: text("corpus_version").notNull(),
  },
  (table) => ({
    // Natural key for idempotent re-ingest: same source + same URL + same
    // corpus version is the "same document". Different corpus versions get
    // their own rows so a reprocessed corpus is preserved. Syndicated content
    // (same content_hash, different URL) stays as distinct documents so the
    // Source Independence Graph can see each copy.
    sourceUrlCorpusIdx: uniqueIndex("documents_source_url_corpus_idx").on(
      table.sourceId,
      table.url,
      table.corpusVersion,
    ),
    // content_hash is still indexed for lookup but NOT unique — two documents
    // can legitimately share a content hash (exact syndication across outlets).
    contentHashIdx: index("documents_content_hash_idx").on(table.contentHash),
    corpusVersionIdx: index("documents_corpus_version_idx").on(table.corpusVersion),
    fetchedAtIdx: index("documents_fetched_at_idx").on(table.fetchedAt),
    sourceIdIdx: index("documents_source_id_idx").on(table.sourceId),
  }),
);

export const documentsRelations = relations(documents, ({ one }) => ({
  source: one(sources, {
    fields: [documents.sourceId],
    references: [sources.id],
  }),
}));

export type Document = typeof documents.$inferSelect;
export type NewDocument = typeof documents.$inferInsert;
