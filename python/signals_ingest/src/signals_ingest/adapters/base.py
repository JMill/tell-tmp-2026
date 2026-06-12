"""Shared ingestion-adapter pipeline.

Every adapter in this package does four things after fetching raw bytes:
extract text with trafilatura, upload the bytes to Blob, upsert a Source
row, and insert a Document row. The Wayback and Direct adapters shipped
their own copies of this code; a new adapter (Reddit, Congressional
records, arXiv, ASRS) would have copied it a third time.

This module owns the shared tail. An adapter builds a ``FetchResult``
with whatever URL resolution and byte-fetching strategy it prefers, then
hands it to ``store_and_index`` which runs the rest of the pipeline and
returns an ``IngestResult``.

The adapter-specific surface area is deliberately small:

    - ``source_name``: human-readable source label
    - ``source_kind``: canonical SourceKind (news, gov, academic, etc.)
    - ``canonical_url``: the authoritative URL for syndicated/archived content
    - ``metadata_extras``: free-form dict merged into the Document's jsonb
    - ``published_at_fallback``: used when trafilatura fails to detect a date
      (Wayback substitutes the snapshot timestamp; Direct has no fallback)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from signals_core import parse_published_at, utcnow

from signals_ingest.extract import extract_from_html
from signals_ingest.storage import (
    BlobPutResult,
    content_hash,
    insert_document,
    put_blob,
    upsert_source,
)


@dataclass
class IngestResult:
    """Result of a single ingestion."""

    document_id: str
    source_id: str
    blob_result: BlobPutResult
    title: str | None
    text_char_count: int


@dataclass
class FetchResult:
    """Everything an adapter must hand to the shared pipeline.

    The adapter owns the fetch phase; this struct describes the handoff
    to the shared store-and-index phase.
    """

    raw_bytes: bytes
    url: str
    domain: str
    source_name: str
    source_kind: str
    canonical_url: str | None = None
    published_at_fallback: datetime | None = None
    metadata_extras: dict[str, Any] = field(default_factory=dict)


_KNOWN_SOURCE_NAMES: dict[str, str] = {
    "nytimes.com": "The New York Times",
    "www.nytimes.com": "The New York Times",
    "washingtonpost.com": "The Washington Post",
    "www.washingtonpost.com": "The Washington Post",
    "wsj.com": "The Wall Street Journal",
    "apnews.com": "The Associated Press",
    "reuters.com": "Reuters",
    "cnn.com": "CNN",
    "nbcnews.com": "NBC News",
    "cbsnews.com": "CBS News",
    "abcnews.go.com": "ABC News",
    "foxnews.com": "Fox News",
    "npr.org": "NPR",
    "thehill.com": "The Hill",
    "politico.com": "Politico",
}


def source_name_from_domain(domain: str) -> str:
    """Humanize a domain into a source name; falls back to the domain."""
    return _KNOWN_SOURCE_NAMES.get(domain, domain)


def store_and_index(
    fetch: FetchResult,
    *,
    corpus_version: str,
    adapter_name: str,
) -> IngestResult:
    """Run the shared extract + hash + blob + upsert + insert pipeline.

    Used by every concrete adapter. The adapter provides a ``FetchResult``
    (raw bytes plus source metadata) and this function does the rest:

        1. Extract text with trafilatura.
        2. Compute the content hash.
        3. Upload raw bytes to Blob at ``corpus/{version}/{domain}/{hash}.html``.
        4. Upsert a Source row.
        5. Insert a Document row carrying the merged metadata.
        6. Return an ``IngestResult``.

    ``adapter_name`` is written into the Document's metadata as
    ``metadata.adapter`` so downstream queries can filter by provenance.
    """
    extracted = extract_from_html(fetch.raw_bytes)
    hash_hex = content_hash(fetch.raw_bytes)

    source_id = upsert_source(
        domain=fetch.domain,
        name=fetch.source_name,
        kind=fetch.source_kind,
    )

    blob_pathname = f"corpus/{corpus_version}/{fetch.domain}/{hash_hex}.html"
    blob_result: BlobPutResult = put_blob(
        pathname=blob_pathname,
        data=fetch.raw_bytes,
        content_type="text/html; charset=utf-8",
        access="private",
    )

    published_at = parse_published_at(extracted.published_at) or fetch.published_at_fallback

    metadata: dict[str, Any] = {
        "adapter": adapter_name,
        "language": extracted.language,
        "author": extracted.author,
        "byte_count": extracted.raw_byte_count,
        "text_char_count": len(extracted.text),
    }
    metadata.update(fetch.metadata_extras)

    document_id = insert_document(
        source_id=source_id,
        url=fetch.url,
        canonical_url=fetch.canonical_url,
        fetched_at=utcnow(),
        published_at=published_at,
        title=extracted.title,
        content_blob_key=blob_pathname,
        content_hash_hex=hash_hex,
        metadata=metadata,
        corpus_version=corpus_version,
    )

    return IngestResult(
        document_id=document_id,
        source_id=source_id,
        blob_result=blob_result,
        title=extracted.title,
        text_char_count=len(extracted.text),
    )
