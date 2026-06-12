"""Wayback Machine adapter.

Fetches archived snapshots of web pages from web.archive.org and passes them
through the standard extraction + storage pipeline.

The Wayback Machine is the first ingestion adapter because it's the single
most reliable way to get a retrospective corpus: news articles from late 2024
are already in the archive, and the archive preserves headers, timestamps, and
content even if the original source has since changed or been paywalled.

Usage:

    # Fetch the most recent snapshot of a URL
    uv run signals ingest wayback --url https://www.nytimes.com/2024/12/12/us/drone-sightings.html

    # Fetch a specific snapshot by timestamp
    uv run signals ingest wayback --url https://... --timestamp 20241212000000
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from signals_core import parse_wayback_timestamp

from .base import (
    FetchResult,
    IngestResult,
    source_name_from_domain,
    store_and_index,
)

WAYBACK_CDX_API = "https://web.archive.org/cdx/search/cdx"
WAYBACK_PREFIX = "https://web.archive.org/web"
USER_AGENT = "signals-pipeline/0.1 (research; +https://github.com/JMill/praxis-deng)"

# Accept: */* is required for the archive.org APIs to return results reliably
# when called from httpx. Observed behavior: default httpx headers produce empty
# responses from both the availability and CDX endpoints in some cases.
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
}

# archive.org throttles and sometimes outright refuses connections when
# hammered by a batch run. Retry with exponential backoff on transient
# failures (ConnectError, ReadTimeout, 429, 503). These constants were
# chosen empirically during the Phase A corpus build — the CDX API can
# take 10+ seconds under load.
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 90.0


# Backwards-compatible alias kept for callers that imported the private
# name from this module. Prefer ``signals_ingest.adapters.base.source_name_from_domain``.
_source_name_from_domain = source_name_from_domain


def _retryable(exc: BaseException) -> bool:
    """Return True if the exception is worth retrying with backoff."""
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 502, 503, 504}
    return False


def _request_with_retry(
    method: str,
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Issue an HTTP request with exponential backoff on transient errors.

    Uses DEFAULT_HEADERS if no override is provided. Always follows redirects.
    Raises the last exception if all retries fail.
    """
    effective_headers = headers if headers is not None else DEFAULT_HEADERS

    last_exc: BaseException | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(
                headers=effective_headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as client:
                response = client.request(method, url, params=params)
                response.raise_for_status()
                return response
        except BaseException as exc:
            if not _retryable(exc) or attempt == MAX_RETRIES - 1:
                raise
            last_exc = exc
            delay = BACKOFF_BASE_SECONDS * (2**attempt)
            time.sleep(delay)

    # Unreachable — the loop either returns or raises
    assert last_exc is not None
    raise last_exc


@dataclass
class WaybackSnapshot:
    """Resolved Wayback snapshot for a URL."""

    original_url: str
    archive_url: str
    timestamp: str  # YYYYMMDDHHMMSS
    status: str  # e.g., "200"


def resolve_snapshot(url: str, timestamp: str | None = None) -> WaybackSnapshot:
    """Resolve a URL to an available Wayback snapshot via the CDX API.

    If `timestamp` is None, returns the most recent successful snapshot
    (status 200). If a specific timestamp is given (YYYYMMDDHHMMSS or a
    prefix like YYYYMMDD), returns the snapshot closest to that time — not
    an exact-second match, which rarely exists in practice. This uses the
    CDX `closest` sort parameter with `limit=1`.

    Raises RuntimeError if no snapshot is available.

    Uses the CDX API instead of the availability API because CDX is more
    reliable and returns structured records directly from the archive index.
    """
    params: dict[str, str] = {
        "url": url,
        "output": "json",
        "filter": "statuscode:200",
    }
    if timestamp:
        # CDX `closest` requires an exact URL match (which we have) and a
        # positive limit. Returns records ordered by proximity to the
        # requested timestamp, so limit=1 gives us the nearest snapshot.
        params["closest"] = timestamp
        params["limit"] = "1"
    else:
        # Negative limit returns the most-recent N rows.
        params["limit"] = "-1"

    response = _request_with_retry("GET", WAYBACK_CDX_API, params=params)
    rows = response.json()

    # CDX returns a JSON array where the first row is the header.
    if not rows or len(rows) < 2:
        raise RuntimeError(f"No Wayback snapshot available for {url}")

    header = rows[0]
    # With both limit=1 (closest) and limit=-1 (most recent), there is
    # exactly one record row after the header.
    record = rows[-1]
    idx = {col: header.index(col) for col in header}

    snap_timestamp = record[idx["timestamp"]]
    original_url = record[idx["original"]]
    statuscode = record[idx["statuscode"]]
    archive_url = f"{WAYBACK_PREFIX}/{snap_timestamp}/{original_url}"

    return WaybackSnapshot(
        original_url=original_url,
        archive_url=archive_url,
        timestamp=snap_timestamp,
        status=statuscode,
    )


def fetch_snapshot(snapshot: WaybackSnapshot) -> bytes:
    """Fetch the raw HTML of a Wayback snapshot.

    Uses the `id_` modifier to get the original content without Wayback's
    injected banner toolbar.
    """
    # Transform https://web.archive.org/web/20241212000000/https://... into
    # https://web.archive.org/web/20241212000000id_/https://... for clean HTML.
    archive_url = snapshot.archive_url
    if "id_" not in archive_url:
        archive_url = archive_url.replace(
            f"/{snapshot.timestamp}/",
            f"/{snapshot.timestamp}id_/",
            1,
        )

    response = _request_with_retry("GET", archive_url)
    return response.content


def ingest_url(
    *,
    url: str,
    corpus_version: str,
    timestamp: str | None = None,
    source_kind: str | None = None,
) -> IngestResult:
    """Ingest a single URL via the Wayback Machine.

    1. Resolve to a Wayback snapshot
    2. Fetch the raw HTML
    3. Hand off to ``store_and_index`` for the shared extract + blob + upsert +
       document-insert tail

    ``source_kind`` is an optional override. When None, defaults to 'news'. The
    batch ingester uses this to pass through the kind declared in seed-urls.yaml.
    """
    snapshot = resolve_snapshot(url, timestamp)
    raw_html = fetch_snapshot(snapshot)

    domain = urlparse(url).netloc.lower()
    fetch = FetchResult(
        raw_bytes=raw_html,
        url=url,
        domain=domain,
        source_name=source_name_from_domain(domain),
        source_kind=source_kind or "news",
        canonical_url=snapshot.archive_url,
        published_at_fallback=parse_wayback_timestamp(snapshot.timestamp),
        metadata_extras={
            "wayback_timestamp": snapshot.timestamp,
            "wayback_status": snapshot.status,
        },
    )

    return store_and_index(
        fetch,
        corpus_version=corpus_version,
        adapter_name="wayback",
    )
