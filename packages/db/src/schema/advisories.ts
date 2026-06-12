/**
 * Prescriptive advisory table: signal-driven recommendations for STAMP
 * controllers.
 *
 * Each advisory maps a signal condition (high IVI, high NVD, low SIG
 * independence, composite capture risk) to a recommended control action
 * for a specific controller. Advisories are template-generated for
 * auditability and reproducibility.
 *
 * Mirrors the pydantic Advisory model in
 * python/signals_core/src/signals_core/models.py
 */
import {
  index,
  jsonb,
  pgEnum,
  pgTable,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const advisoryType = pgEnum("advisory_type", [
  "act",
  "investigate",
  "monitor",
  "disclose",
]);

export const advisorySeverity = pgEnum("advisory_severity", [
  "watch",
  "advisory",
  "alert",
]);

export const advisoryStatus = pgEnum("advisory_status", [
  "open",
  "acknowledged",
  "acted",
  "dismissed",
  "superseded",
]);

export const advisories = pgTable(
  "advisories",
  {
    id: text("id").primaryKey(), // ULID
    topic: text("topic").notNull(),
    corpusVersion: text("corpus_version").notNull(),
    controllerSlug: text("controller_slug").notNull(),
    narrativeSlug: text("narrative_slug").notNull().default(""),
    signalTrigger: text("signal_trigger").notNull(),
    signalValues: jsonb("signal_values").$type<Record<string, number>>(),
    advisoryType: advisoryType("advisory_type").notNull(),
    severity: advisorySeverity("severity").notNull(),
    recommendation: text("recommendation").notNull(),
    rationale: text("rationale").notNull(),
    kleinActivity: text("klein_activity"),
    stampFailureMode: text("stamp_failure_mode").notNull(),
    status: advisoryStatus("status").notNull().default("open"),
    advisoryDate: timestamp("advisory_date", { withTimezone: true }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    resolvedAt: timestamp("resolved_at", { withTimezone: true }),
  },
  (table) => ({
    topicCorpusControllerTriggerNarrativeDateIdx: uniqueIndex(
      "advisories_topic_corpus_ctrl_trigger_narr_date_idx",
    ).on(
      table.topic,
      table.corpusVersion,
      table.controllerSlug,
      table.signalTrigger,
      table.narrativeSlug,
      table.advisoryDate,
    ),
    corpusIdx: index("advisories_corpus_idx").on(table.corpusVersion),
    controllerIdx: index("advisories_controller_idx").on(table.controllerSlug),
    severityIdx: index("advisories_severity_idx").on(table.severity),
    statusIdx: index("advisories_status_idx").on(table.status),
    advisoryDateIdx: index("advisories_advisory_date_idx").on(table.advisoryDate),
  }),
);

export type AdvisoryRow = typeof advisories.$inferSelect;
export type NewAdvisoryRow = typeof advisories.$inferInsert;
