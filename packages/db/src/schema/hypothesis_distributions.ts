/**
 * Daily hypothesis distributions per topic.
 *
 * Aggregated from document_hypothesis_scores. Each row is the H1-H5
 * distribution for a (topic, day) pair, plus entropy and modal hypothesis.
 *
 * Used by the Sensemaking Quality Metrics (SQM) calculations downstream
 * and by the dashboard's hypothesis-distribution chart.
 *
 * The distribution is stored as a jsonb object {H1: 0.20, H2: 0.10, ...}
 * rather than five separate columns so adding H6 (or any future hypothesis)
 * does not require a schema migration.
 */
import { index, integer, jsonb, pgTable, real, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const hypothesisDistributions = pgTable(
  "hypothesis_distributions",
  {
    id: text("id").primaryKey(), // ULID
    topic: text("topic").notNull(),
    corpusVersion: text("corpus_version").notNull(),
    day: timestamp("day", { withTimezone: true }).notNull(),
    documentCount: integer("document_count").notNull(),
    distribution: jsonb("distribution").$type<Record<string, number>>().notNull(),
    entropy: real("entropy").notNull(), // Shannon entropy in bits, max log2(5) ≈ 2.32
    modalHypothesis: text("modal_hypothesis").notNull(), // H1..H5
    modalProbability: real("modal_probability").notNull(),
    promptVersion: text("prompt_version").notNull(),
    model: text("model").notNull(),
    computedAt: timestamp("computed_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    // Unique constraint includes corpus_version so runs against different
    // corpus versions coexist rather than clobbering each other.
    topicDayIdx: uniqueIndex("hyp_dist_topic_corpus_day_idx").on(
      table.topic,
      table.corpusVersion,
      table.day,
      table.promptVersion,
      table.model,
    ),
    corpusIdx: index("hyp_dist_corpus_idx").on(table.corpusVersion),
    dayIdx: index("hyp_dist_day_idx").on(table.day),
  }),
);

export type HypothesisDistributionRow = typeof hypothesisDistributions.$inferSelect;
export type NewHypothesisDistributionRow = typeof hypothesisDistributions.$inferInsert;
