"""Storage helpers: Vercel Blob and Neon Postgres.

Blob upload and credential handling live in the standalone
``vercel_blob_client`` package. Postgres access comes from
``signals_core``. This module keeps the TELL-specific SQL (Source and
Document upsert/insert, corpus counts) and re-exports the Blob helpers
at their original names so existing callers are unaffected.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import psycopg
from signals_core import neon_connection, utcnow
from vercel_blob_client import (
    VERCEL_BLOB_API,
    VERCEL_BLOB_API_VERSION,
    BlobPutResult,
    get_blob_token,
)
from vercel_blob_client import put as put_blob


def content_hash(data: bytes) -> str:
    """SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


__all__ = [
    "VERCEL_BLOB_API",
    "VERCEL_BLOB_API_VERSION",
    "BlobPutResult",
    "content_hash",
    "get_blob_token",
    "put_blob",
    # Plus the TELL-specific helpers defined below.
]


def upsert_source(
    *,
    domain: str,
    name: str,
    kind: str,
) -> str:
    """Upsert a Source row and return its id.

    If a source with this domain already exists, update its kind if it
    changed and return its id. Otherwise insert a new row.
    """
    from ulid import ULID

    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, kind FROM sources WHERE domain = %s",
            (domain,),
        )
        row = cur.fetchone()
        if row:
            # Update kind if it changed (fixes reclassification on re-ingest)
            if row["kind"] != kind:
                cur.execute(
                    "UPDATE sources SET kind = %s WHERE id = %s",
                    (kind, row["id"]),
                )
            return row["id"]

        source_id = str(ULID())
        cur.execute(
            """
                INSERT INTO sources (id, domain, name, kind, first_seen_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
            (source_id, domain, name, kind, utcnow()),
        )
        return source_id


def insert_document(
    *,
    source_id: str,
    url: str,
    canonical_url: str | None,
    fetched_at: datetime,
    published_at: datetime | None,
    title: str | None,
    content_blob_key: str | None,
    content_hash_hex: str,
    metadata: dict[str, Any],
    corpus_version: str,
) -> str:
    """Insert or update a Document row and return its id.

    Idempotency is keyed on the natural composite (source_id, url,
    corpus_version). Re-ingesting the same URL from the same source into the
    same corpus updates the row in place (fetched_at, metadata, content_hash,
    content_blob_key) so the latest fetch is authoritative. Ingesting into a
    different corpus version creates a new row. Syndicated content (same
    content_hash but different URL or different source) creates distinct rows
    so the Source Independence Graph can see each copy.

    Returns the document id — the pre-existing id if an ON CONFLICT update
    fired, otherwise the newly-generated ULID.
    """
    from ulid import ULID

    doc_id = str(ULID())
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO documents (
                    id, source_id, url, canonical_url, fetched_at, published_at,
                    title, content_blob_key, content_hash, metadata, corpus_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (source_id, url, corpus_version) DO UPDATE
                    SET fetched_at = EXCLUDED.fetched_at,
                        published_at = COALESCE(EXCLUDED.published_at, documents.published_at),
                        title = COALESCE(EXCLUDED.title, documents.title),
                        content_hash = EXCLUDED.content_hash,
                        content_blob_key = EXCLUDED.content_blob_key,
                        canonical_url = COALESCE(EXCLUDED.canonical_url, documents.canonical_url),
                        metadata = documents.metadata || EXCLUDED.metadata
                RETURNING id
                """,
            (
                doc_id,
                source_id,
                url,
                canonical_url,
                fetched_at,
                published_at,
                title,
                content_blob_key,
                content_hash_hex,
                psycopg.types.json.Jsonb(metadata),
                corpus_version,
            ),
        )
        row = cur.fetchone()
        return row["id"] if row else doc_id


def document_count(corpus_version: str | None = None) -> int:
    """Count documents in the database, optionally filtered by corpus_version."""
    with neon_connection() as conn, conn.cursor() as cur:
        if corpus_version:
            cur.execute(
                "SELECT COUNT(*)::int AS n FROM documents WHERE corpus_version = %s",
                (corpus_version,),
            )
        else:
            cur.execute("SELECT COUNT(*)::int AS n FROM documents")
        row = cur.fetchone()
        return row["n"] if row else 0
