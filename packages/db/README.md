# @tells-fyi/db

Drizzle ORM schema and Neon Postgres client for the TELL weak-signal detection pipeline.

## Schema

Defined in `src/schema/`:

- **`sources`** — where documents originate (news outlets, government agencies, social, academic, etc.)
- **`documents`** — individual fetched documents with metadata (raw content lives in Vercel Blob)
- **`corpus_versions`** — frozen snapshots for reproducibility

Cross-references the pydantic source-of-truth models at `python/signals_core/src/signals_core/models.py`. A schema sync CI job keeps them aligned.

## Commands

```bash
# Generate a migration (for version control)
pnpm --filter @tells-fyi/db db:generate

# Push schema directly to the database (dev-only)
pnpm --filter @tells-fyi/db db:push

# Open Drizzle Studio
pnpm --filter @tells-fyi/db db:studio
```

All commands require `DATABASE_URL` (or `DATABASE_URL_UNPOOLED`) in the environment. Pull it with `vercel env pull .env.local` from the pipeline root and source the file.

## Usage

```ts
import { db, tables } from "@tells-fyi/db";
import { eq } from "drizzle-orm";

const docs = await db
  .select()
  .from(tables.documents)
  .where(eq(tables.documents.corpusVersion, "nj-drones-2026-04-07"));
```
