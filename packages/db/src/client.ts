/**
 * Neon Postgres client + Drizzle instance.
 *
 * Uses @neondatabase/serverless for serverless-friendly HTTP/WebSocket access.
 * Callers should import `db` and use Drizzle's query builder directly.
 */
import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";

import * as schema from "./schema";

function getDatabaseUrl(): string {
  // Prefer the Neon integration's gray-mirror var when present (Vercel),
  // fall back to DATABASE_URL (local dev via .env.local).
  const url =
    process.env.database_POSTGRES_PRISMA_URL || process.env.DATABASE_URL;
  if (!url) {
    throw new Error(
      "DATABASE_URL is not set. Run `vercel env pull .env.local` from dev/tell/ and load it.",
    );
  }
  return url;
}

export function createDb() {
  const sql = neon(getDatabaseUrl());
  return drizzle(sql, { schema });
}

export const db = createDb();
export { schema };
export type Database = ReturnType<typeof createDb>;
