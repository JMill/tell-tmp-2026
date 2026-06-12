/**
 * Source Independence Graph (SIG) results per narrative.
 *
 * One row per (topic, corpus_version, narrative_slug). Stores the computed
 * independence score and amplification ratio for each narrative, plus a
 * graph_data jsonb blob containing the per-source-domain detail for
 * rendering the independence graph on the dashboard.
 *
 * independence_score = independent_sources + 1 (the originating source).
 * amplification_ratio = total_documents / independence_score.
 *
 * A narrative with independence_score == 1 and high amplification_ratio
 * is a canonical echo chamber.
 */
import { index, integer, jsonb, pgTable, real, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const signalIndependence = pgTable(
  "signal_independence",
  {
    id: text("id").primaryKey(),
    topic: text("topic").notNull(),
    corpusVersion: text("corpus_version").notNull(),
    narrativeSlug: text("narrative_slug").notNull(),
    narrativeLabel: text("narrative_label").notNull(),
    originLabel: text("origin_label").notNull(),
    totalDocuments: integer("total_documents").notNull(),
    uniqueDomains: integer("unique_domains").notNull(),
    independentSources: integer("independent_sources").notNull(),
    amplifierSources: integer("amplifier_sources").notNull(),
    independenceScore: real("independence_score").notNull(),
    amplificationRatio: real("amplification_ratio").notNull(),
    graphData: jsonb("graph_data").$type<{ sources: Array<{ domain: string; role: string; document_count: number }> }>().notNull().default({ sources: [] }),
    computedAt: timestamp("computed_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    uniqueIdx: uniqueIndex("signal_independence_unique_idx").on(
      table.topic,
      table.corpusVersion,
      table.narrativeSlug,
    ),
    topicCorpusIdx: index("signal_independence_topic_corpus_idx").on(table.topic, table.corpusVersion),
  }),
);

export type SignalIndependenceRow = typeof signalIndependence.$inferSelect;
export type NewSignalIndependenceRow = typeof signalIndependence.$inferInsert;
