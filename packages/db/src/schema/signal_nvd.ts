/**
 * Narrative Velocity Divergence (NVD) time series.
 *
 * One row per (topic, corpus_version, narrative_slug, window_end, window_days).
 * narrative_velocity: documents matching the narrative in the rolling window.
 * evidence_velocity: documents with hypothesis-supported evidence in the window.
 * nvd_value: narrative_velocity / (evidence_velocity + 1).
 *
 * Used by the dashboard NVD chart and by the SQM evaluation.
 */
import { index, integer, pgTable, real, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const signalNvd = pgTable(
  "signal_nvd",
  {
    id: text("id").primaryKey(),
    topic: text("topic").notNull(),
    corpusVersion: text("corpus_version").notNull(),
    narrativeSlug: text("narrative_slug").notNull(),
    windowStart: timestamp("window_start", { withTimezone: true }).notNull(),
    windowEnd: timestamp("window_end", { withTimezone: true }).notNull(),
    windowDays: integer("window_days").notNull(),
    narrativeVelocity: integer("narrative_velocity").notNull(),
    evidenceVelocity: integer("evidence_velocity").notNull(),
    nvdValue: real("nvd_value").notNull(),
    computedAt: timestamp("computed_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    uniqueIdx: uniqueIndex("signal_nvd_unique_idx").on(
      table.topic,
      table.corpusVersion,
      table.narrativeSlug,
      table.windowEnd,
      table.windowDays,
    ),
    topicCorpusIdx: index("signal_nvd_topic_corpus_idx").on(table.topic, table.corpusVersion),
  }),
);

export type SignalNvdRow = typeof signalNvd.$inferSelect;
export type NewSignalNvdRow = typeof signalNvd.$inferInsert;
