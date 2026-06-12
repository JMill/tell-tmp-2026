"""Tests for the shared adapter base (FetchResult + store_and_index).

The network-touching halves of store_and_index (Blob upload, Neon upsert)
are covered by the scripts/smoke-test.sh integration check. This file
covers the pure parts: source-name humanization and FetchResult defaults.
"""

from __future__ import annotations

from signals_ingest.adapters.base import (
    FetchResult,
    source_name_from_domain,
)


def test_source_name_known_domains() -> None:
    assert source_name_from_domain("nytimes.com") == "The New York Times"
    assert source_name_from_domain("www.nytimes.com") == "The New York Times"
    assert source_name_from_domain("npr.org") == "NPR"
    assert source_name_from_domain("politico.com") == "Politico"


def test_source_name_unknown_domain_passes_through() -> None:
    assert source_name_from_domain("example.com") == "example.com"
    assert source_name_from_domain("some.obscure.tld") == "some.obscure.tld"


def test_fetch_result_defaults() -> None:
    fr = FetchResult(
        raw_bytes=b"<html></html>",
        url="https://example.com/post",
        domain="example.com",
        source_name="Example",
        source_kind="news",
    )
    assert fr.canonical_url is None
    assert fr.published_at_fallback is None
    assert fr.metadata_extras == {}


def test_fetch_result_accepts_extras() -> None:
    fr = FetchResult(
        raw_bytes=b"",
        url="u",
        domain="d",
        source_name="n",
        source_kind="k",
        metadata_extras={"wayback_status": "200"},
    )
    assert fr.metadata_extras["wayback_status"] == "200"
