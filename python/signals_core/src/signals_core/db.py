"""Neon Postgres connection helpers.

Three TELL packages (signals_ingest, signals_analyze, signals_methods) each
previously carried their own ``neon_connection()`` context manager and
``get_database_url()`` helper. They live here now with matching semantics:
the unpooled URL is preferred (long-running batch work dislikes pgbouncer),
every connection yields a ``dict_row`` cursor by default, commits on clean
exit, rolls back on exception, and always closes.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

DATABASE_URL_ENV_HINT = (
    "DATABASE_URL not set. Run `vercel env pull .env.local` from "
    "dev/tell/ and load the file into your shell environment."
)


def get_database_url() -> str:
    """Return the Postgres connection string.

    Prefers ``DATABASE_URL_UNPOOLED`` over ``DATABASE_URL``. Batch work
    (ingestion, scoring, signal computation) benefits from a direct
    connection; Vercel serverless paths should pass ``DATABASE_URL``
    explicitly via an override layer instead of mutating env.
    """
    url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(DATABASE_URL_ENV_HINT)
    return url


@contextmanager
def neon_connection() -> Iterator[psycopg.Connection]:
    """Open a connection to Neon Postgres with transactional semantics.

    Use as a context manager::

        with neon_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

    On clean exit the connection commits. On any exception it rolls back
    and re-raises. The connection is always closed on exit.
    """
    conn = psycopg.connect(get_database_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
