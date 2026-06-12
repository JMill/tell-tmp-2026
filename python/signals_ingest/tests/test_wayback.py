"""Unit tests for the Wayback adapter's pure functions.

Network-touching functions (resolve_snapshot, fetch_snapshot, ingest_url) are
intentionally NOT tested here because they depend on archive.org and on live
Neon + Blob credentials. Those are covered by the scripts/smoke-test.sh
integration check instead.

Run with: uv run pytest python/signals_ingest/tests/test_wayback.py
"""

from datetime import UTC

from signals_core import parse_wayback_timestamp as _parse_wayback_timestamp
from signals_ingest.adapters.wayback import (
    DEFAULT_HEADERS,
    WaybackSnapshot,
    _source_name_from_domain,
)


def test_default_headers_has_accept() -> None:
    """Regression test: the Wayback CDX API silently returns empty results
    over httpx unless Accept: */* is explicitly set. This caused a hard-to-
    debug failure during Stage 2. Keep this header."""
    assert DEFAULT_HEADERS.get("Accept") == "*/*"
    assert "User-Agent" in DEFAULT_HEADERS


def test_parse_wayback_timestamp() -> None:
    """Wayback timestamps are YYYYMMDDHHMMSS UTC strings."""
    dt = _parse_wayback_timestamp("20241212153045")
    assert dt.year == 2024
    assert dt.month == 12
    assert dt.day == 12
    assert dt.hour == 15
    assert dt.minute == 30
    assert dt.second == 45
    assert dt.tzinfo == UTC


def test_source_name_from_domain_known() -> None:
    """Known news domains get humanized names."""
    assert _source_name_from_domain("nytimes.com") == "The New York Times"
    assert _source_name_from_domain("www.nytimes.com") == "The New York Times"
    assert _source_name_from_domain("npr.org") == "NPR"


def test_source_name_from_domain_unknown() -> None:
    """Unknown domains fall back to the domain string itself."""
    assert _source_name_from_domain("some-random-blog.example") == "some-random-blog.example"


def test_wayback_snapshot_dataclass() -> None:
    """Snapshot dataclass round-trips field values."""
    snap = WaybackSnapshot(
        original_url="https://example.com",
        archive_url="https://web.archive.org/web/20241212000000/https://example.com",
        timestamp="20241212000000",
        status="200",
    )
    assert snap.original_url == "https://example.com"
    assert snap.timestamp == "20241212000000"
