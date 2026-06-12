/**
 * Source table — where documents come from.
 *
 * Mirrors the pydantic Source model in
 * python/signals_core/src/signals_core/models.py
 */
import { jsonb, pgEnum, pgTable, real, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const sourceKind = pgEnum("source_kind", [
  "gov",
  "news",
  "social",
  "academic",
  "aviation",
  "forum",
  "podcast",
  "other",
]);

export const sources = pgTable(
  "sources",
  {
    id: text("id").primaryKey(), // ULID
    domain: text("domain").notNull(),
    name: text("name").notNull(),
    kind: sourceKind("kind").notNull(),
    reliabilityScore: real("reliability_score"),
    reliabilityFactors: jsonb("reliability_factors").$type<Record<string, unknown>>(),
    firstSeenAt: timestamp("first_seen_at", { withTimezone: true }).notNull(),
  },
  (table) => ({
    domainIdx: uniqueIndex("sources_domain_idx").on(table.domain),
  }),
);

export type Source = typeof sources.$inferSelect;
export type NewSource = typeof sources.$inferInsert;
