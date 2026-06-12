"""Tests for vercel_blob_client that do not touch the network."""

from __future__ import annotations

import pytest
from vercel_blob_client import (
    BlobPutResult,
    get_blob_store_id,
    get_blob_token,
)


def test_get_blob_token_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="BLOB_READ_WRITE_TOKEN"):
        get_blob_token()


def test_get_blob_token_returns_env_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "vercel_blob_rw_abc123store_somehash")
    assert get_blob_token() == "vercel_blob_rw_abc123store_somehash"


def test_get_blob_store_id_from_token() -> None:
    assert get_blob_store_id("vercel_blob_rw_MyStoreID_abcdefgh") == "mystoreid"


def test_get_blob_store_id_bad_format_raises() -> None:
    with pytest.raises(RuntimeError, match="Unexpected BLOB_READ_WRITE_TOKEN format"):
        get_blob_store_id("notatoken")


def test_blob_put_result_optional_content_disposition() -> None:
    result = BlobPutResult(
        url="https://example",
        pathname="a/b.html",
        size=42,
        content_type="text/html",
    )
    assert result.content_disposition is None
