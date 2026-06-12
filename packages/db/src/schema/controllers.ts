/**
 * STAMP controller table: institutional actors in the information-environment
 * control structure.
 *
 * Controllers are loaded from data/{topic}/controllers.yaml and persisted here
 * for the dashboard to query. Each controller has a STAMP role (controller,
 * actuator, sensor), a jurisdiction, and a set of available control actions.
 *
 * Mirrors the pydantic Controller model in
 * python/signals_core/src/signals_core/models.py
 */
import { jsonb, pgEnum, pgTable, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const controllerRole = pgEnum("controller_role", [
  "institutional",
  "political",
  "media",
  "analyst",
]);

export const stampFunction = pgEnum("stamp_function", [
  "controller",
  "actuator",
  "sensor",
]);

export const controllers = pgTable(
  "controllers",
  {
    id: text("id").primaryKey(), // ULID
    topic: text("topic").notNull(),
    slug: text("slug").notNull(),
    label: text("label").notNull(),
    role: controllerRole("role").notNull(),
    stampFunction: stampFunction("stamp_function").notNull(),
    jurisdiction: text("jurisdiction").notNull(),
    availableActions: jsonb("available_actions").$type<
      Array<{ type: string; label: string }>
    >(),
    informationNeeds: jsonb("information_needs").$type<string[]>(),
    narratives: jsonb("narratives").$type<
      Array<{ slug: string; relationship: string }>
    >(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    topicSlugIdx: uniqueIndex("controllers_topic_slug_idx").on(table.topic, table.slug),
  }),
);

export type ControllerRow = typeof controllers.$inferSelect;
export type NewControllerRow = typeof controllers.$inferInsert;
