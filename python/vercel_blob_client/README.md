# vercel-blob-client

A Python REST client for [Vercel Blob](https://vercel.com/docs/storage/vercel-blob).

## Why this exists

Vercel publishes `@vercel/blob` for JavaScript/TypeScript but does not ship a
Python SDK. The upload endpoint (`https://vercel.com/api/blob?pathname=...`)
and the custom headers (`x-api-version`, `x-vercel-blob-access`,
`x-add-random-suffix`, `x-allow-overwrite`, `x-content-type`) are not publicly
documented. Private-blob fetch needs a bearer token against
`https://{storeId}.private.blob.vercel-storage.com/{key}`. This package
contains a production-proven implementation of both, reverse-engineered from
the `@vercel/blob` source (`dist/chunk-*.js`) and validated end-to-end
against the TELL pipeline's NJ-drones corpus (204 documents, several GB
through the API without incident).

## Install

Part of the TELL monorepo and installable from source:

```bash
pip install -e dev/tell/python/vercel_blob_client
```

A standalone PyPI release is not published yet. When it is, the canonical name
will be `vercel-blob-client`.

## Scope

- `put(...)` — upload bytes to a private or public blob.
- `fetch(key)` — GET the raw bytes of a private blob.
- `BlobPutResult` — dataclass describing the API response.
- `get_blob_token()`, `get_blob_store_id()` — helpers that read
  `BLOB_READ_WRITE_TOKEN` from the environment and extract the store id.
- `VERCEL_BLOB_API`, `VERCEL_BLOB_API_VERSION` — the endpoint and header
  version this client speaks to.

No uploads depend on a pre-resolved upload URL; the client speaks directly to
`vercel.com/api/blob`.

## Usage

```python
from vercel_blob_client import put, fetch

result = put(
    pathname="corpus/v1/doc.html",
    data=b"<html>...</html>",
    content_type="text/html; charset=utf-8",
    access="private",
)
print(result.url)

raw = fetch("corpus/v1/doc.html")
```

### API

```python
def put(
    *,
    pathname: str,
    data: bytes,
    content_type: str,
    access: str = "private",
    add_random_suffix: bool = False,
    allow_overwrite: bool = True,
    timeout_seconds: float = 60.0,
    token: str | None = None,
) -> BlobPutResult: ...

def fetch(
    blob_key: str,
    *,
    timeout_seconds: float = 60.0,
    token: str | None = None,
    store_id: str | None = None,
) -> bytes: ...
```

`put` returns a `BlobPutResult(url, pathname, size, content_type,
content_disposition)`. `fetch` returns raw bytes.

### Errors

Both functions raise `RuntimeError` when `BLOB_READ_WRITE_TOKEN` is missing or
malformed, and propagate `httpx.HTTPStatusError` for non-2xx responses
(including the 429, 502, 503, and 504 that Vercel occasionally returns under
load). Retry policy is the caller's responsibility; the client does one
attempt with a 60-second default timeout.

## Environment

Requires `BLOB_READ_WRITE_TOKEN` to be set. The token format
`vercel_blob_rw_<storeId>_<hash>` encodes the store id; `get_blob_store_id()`
extracts it. Pull the token into a local `.env.local` with:

```bash
vercel env pull .env.local
```

## Testing

Unit tests live in `tests/test_client.py` and exercise only the non-network
pure functions (token parsing, store-id extraction, dataclass defaults).
End-to-end validation runs through the TELL pipeline's smoke test,
`dev/tell/scripts/smoke-test.sh`.

```bash
pip install -e .[dev]
pytest tests/
```

## Citing

A machine-readable `CITATION.cff` is included at the package root. BibTeX:

```bibtex
@software{miller_vercel_blob_client_2026,
  author = {Miller, Jonathan},
  title  = {vercel-blob-client: Reverse-engineered Python REST client for Vercel Blob},
  year   = {2026},
  url    = {https://github.com/JMill/praxis-deng/tree/main/dev/tell/python/vercel_blob_client}
}
```

## License

TBD. The package ships without a SPDX-listed license as of 2026-04. Contact
JMill before redistribution.
