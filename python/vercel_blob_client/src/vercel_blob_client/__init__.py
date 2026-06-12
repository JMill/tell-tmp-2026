"""Reverse-engineered Python client for the Vercel Blob REST API.

The public REST endpoint is ``https://vercel.com/api/blob?pathname=...``.
Private blobs are fetched against
``https://{storeId}.private.blob.vercel-storage.com/{key}`` with a bearer
token. Neither surface is documented; both are reverse-engineered from
the ``@vercel/blob`` JavaScript SDK (``dist/chunk-*.js``) and validated
against the TELL pipeline's production corpus.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

# Reverse-engineered from @vercel/blob source (dist/chunk-*.js).
# The public REST endpoint is vercel.com/api/blob, not blob.vercel-storage.com
# (the latter is where blob URLs resolve, not the upload endpoint).
VERCEL_BLOB_API = "https://vercel.com/api/blob"
VERCEL_BLOB_API_VERSION = "12"

_DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass
class BlobPutResult:
    """Metadata returned by the Vercel Blob upload endpoint."""

    url: str
    pathname: str
    size: int
    content_type: str
    content_disposition: str | None = None


def get_blob_token() -> str:
    """Return the Vercel Blob read/write token from the environment.

    Raises ``RuntimeError`` if ``BLOB_READ_WRITE_TOKEN`` is not set.
    """
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise RuntimeError(
            "BLOB_READ_WRITE_TOKEN not set. Pull it with `vercel env pull .env.local` "
            "from the project root and load the file into your shell environment."
        )
    return token


def get_blob_store_id(token: str | None = None) -> str:
    """Extract the store id from a ``BLOB_READ_WRITE_TOKEN``.

    Token format: ``vercel_blob_rw_<storeId>_<hash>``. If ``token`` is not
    provided, it is read from the environment.
    """
    raw = token if token is not None else get_blob_token()
    parts = raw.split("_")
    if len(parts) < 4:
        raise RuntimeError("Unexpected BLOB_READ_WRITE_TOKEN format")
    return parts[3].lower()


def put(
    *,
    pathname: str,
    data: bytes,
    content_type: str,
    access: str = "private",
    add_random_suffix: bool = False,
    allow_overwrite: bool = True,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    token: str | None = None,
) -> BlobPutResult:
    """Upload bytes to Vercel Blob and return the response metadata.

    The call hits ``https://vercel.com/api/blob?pathname=...`` with headers
    modeled after the ``@vercel/blob`` SDK: ``authorization``, ``x-api-version``,
    ``x-vercel-blob-access``, ``x-content-type``, ``x-add-random-suffix``,
    and ``x-allow-overwrite``.

    Parameters
    ----------
    pathname:
        Key under which to store the blob, e.g. ``corpus/v1/abc123.html``.
    data:
        Raw bytes to upload.
    content_type:
        MIME type. Written into the ``x-content-type`` header and returned
        on the response if the API does not echo a different value.
    access:
        ``public`` or ``private``. Must match the store-level access.
    add_random_suffix:
        If ``True``, Vercel appends a random suffix to the URL. Default
        ``False`` keeps the URL deterministic from the pathname.
    allow_overwrite:
        If ``True``, overwrite any existing blob at this pathname.
    timeout_seconds:
        HTTP timeout. Defaults to 60 seconds.
    token:
        Override the ``BLOB_READ_WRITE_TOKEN`` environment variable for a
        single call.
    """
    bearer = token if token is not None else get_blob_token()
    headers = {
        "authorization": f"Bearer {bearer}",
        "x-api-version": VERCEL_BLOB_API_VERSION,
        "x-vercel-blob-access": access,
        "x-content-type": content_type,
        "x-add-random-suffix": "1" if add_random_suffix else "0",
        "x-allow-overwrite": "1" if allow_overwrite else "0",
    }

    url = f"{VERCEL_BLOB_API}/?pathname={pathname.lstrip('/')}"
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.put(url, content=data, headers=headers)
        response.raise_for_status()
        body = response.json()

    return BlobPutResult(
        url=body["url"],
        pathname=body["pathname"],
        size=body.get("size", len(data)),
        content_type=body.get("contentType", content_type),
        content_disposition=body.get("contentDisposition"),
    )


def fetch(
    blob_key: str,
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    token: str | None = None,
    store_id: str | None = None,
) -> bytes:
    """Fetch raw bytes from a private Vercel Blob by key.

    The Blob URL pattern is
    ``https://{storeId}.private.blob.vercel-storage.com/{key}`` and private
    blobs require an ``Authorization: Bearer <token>`` header.

    ``store_id`` defaults to the value extracted from ``BLOB_READ_WRITE_TOKEN``.
    """
    bearer = token if token is not None else get_blob_token()
    resolved_store_id = store_id if store_id is not None else get_blob_store_id(bearer)
    url = f"https://{resolved_store_id}.private.blob.vercel-storage.com/{blob_key}"
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(url, headers={"Authorization": f"Bearer {bearer}"})
        response.raise_for_status()
        return response.content


__all__ = [
    "VERCEL_BLOB_API",
    "VERCEL_BLOB_API_VERSION",
    "BlobPutResult",
    "fetch",
    "get_blob_store_id",
    "get_blob_token",
    "put",
]
