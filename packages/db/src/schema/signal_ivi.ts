/**
 * Information Vacuum Index (IVI) time series.
 *
 * One row per (topic, window_end, window_days) triple. The unique index
 * makes recomputes idempotent — running `signals compute ivi` against
 * the same corpus with the same window length overwrites prior rows for
 * that window end rather than duplicating.
 *
 * Mirrors the pydantic model in
 * python/signals_core/src/signals_core/models.py and the method
 * implementation in
 * python/signals_methods/src/signals_methods/ivi.py.
 */
import {
  index,
  integer,
  jsonb,
  pgTable,
  real,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const signalIvi = pgTable(
  "signal_ivi",
  {
    id: text("id").primaryKey(), // ULID
    topic: text("topic").notNull(),
    corpusVersion: text("corpus_version").notNull(),
    windowStart: timestamp("window_start", { withTimezone: true }).notNull(),
    windowEnd: timestamp("window_end", { withTimezone: true }).notNull(),
    windowDays: integer("window_days").notNull(),
    discourseCount: integer("discourse_count").notNull(),
    authoritativeCount: integer("authoritative_count").notNull(),
    value: real("value").notNull(),
    components: jsonb("components").$type<Record<string, unknown>>(),
    computedAt: timestamp("computed_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    topicWindowIdx: uniqueIndex("signal_ivi_topic_window_idx").on(
      table.topic,
      table.windowEnd,
      table.windowDays,
    ),
    corpusIdx: index("signal_ivi_corpus_idx").on(table.corpusVersion),
    windowEndIdx: index("signal_ivi_window_end_idx").on(table.windowEnd),
  }),
);

export type SignalIviRow = typeof signalIvi.$inferSelect;
export type NewSignalIviRow = typeof signalIvi.$inferInsert;
