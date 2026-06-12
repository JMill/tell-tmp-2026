"""HTML content extraction built on trafilatura.

Thin wrapper that every pipeline layer needs and that two packages
(signals_ingest and signals_analyze) previously carried a copy of. The
signals_analyze copy had a docstring acknowledging the duplication and
kept it anyway to avoid a cross-package import. Now that signals_core
owns utilities, the duplication is gone.

The returned ``ExtractedContent`` carries the full metadata set that
trafilatura produces: title, author, ISO 8601 published_at, and language.
Callers that only care about the title or text can ignore the rest.
"""

from __future__ import annotations

from dataclasses import dataclass

import trafilatura


@dataclass(frozen=True)
class ExtractedContent:
    """Result of a content extraction pass."""

    title: str | None
    text: str
    author: str | None
    published_at: str | None  # ISO 8601 if trafilatura detected one
    language: str | None
    raw_byte_count: int


def extract_from_html(html: str | bytes) -> ExtractedContent:
    """Extract readable text and metadata from raw HTML.

    Uses ``trafilatura.extract`` with ``favor_recall=True``, tables
    included, comments excluded, and plain-text output. Metadata is
    pulled from ``trafilatura.extract_metadata``.

    Raises ``ValueError`` if the HTML is empty or if trafilatura returns
    no main content.
    """
    if not html:
        raise ValueError("Empty HTML input")

    html_str = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
    byte_count = len(html_str.encode("utf-8"))

    metadata = trafilatura.extract_metadata(html_str)
    text = trafilatura.extract(
        html_str,
        output_format="txt",
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )

    if text is None or not text.strip():
        raise ValueError("No main content could be extracted from HTML")

    return ExtractedContent(
        title=metadata.title if metadata else None,
        text=text,
        author=metadata.author if metadata else None,
        published_at=metadata.date if metadata else None,
        language=metadata.language if metadata else None,
        raw_byte_count=byte_count,
    )
