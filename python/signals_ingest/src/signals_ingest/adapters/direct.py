"""Direct HTTP adapter.

Fetches a URL directly from the live web. Use for sources that are
(a) still live, (b) not rate-limited, and (c) ideally served without
authentication. Canonical use cases: government press releases, FBI/DHS
archive pages, podcast RSS entries, long-stable institutional URLs.

If the direct fetch fails (non-200, DNS failure, timeout) the caller
can choose to fall back to the Wayback adapter.

Unlike the Wayback adapter, this adapter does NOT provide point-in-time
snapshots — it fetches whatever is currently live. For retrospective
research where point-in-time integrity matters, prefer Wayback. For
government sources that rarely change and have long-stable URLs, direct
is cheaper and gives the authoritative copy.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from .base import FetchResult, IngestResult, source_name_from_domain, store_and_index

USER_AGENT = "signals-pipeline/0.1 (research; +https://github.com/JMill/praxis-deng)"

# Accept a broader set of content types than a default httpx client.
# Some sites return text/html only if Accept includes it explicitly.
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# Known social-media hosts. Matched exactly or as a subdomain (e.g.
# www.x.com matches "x.com" but fox.com does NOT match "x.com" because it
# neither equals "x.com" nor ends with ".x.com"). This prevents the
# substring-match bug where "x.com" in domain would incorrectly classify
# fox.com and examplex.com as social.
_SOCIAL_HOSTS: frozenset[str] = frozenset(
    {
        "reddit.com",
        "bsky.app",
        "twitter.com",
        "x.com",
        "threads.net",
        "mastodon.social",
    }
)

# Known podcast hosts. Same exact/subdomain matching rule.
_PODCAST_HOSTS: frozenset[str] = frozenset(
    {
        "podcasts.apple.com",
        "podcasts.google.com",
        "open.spotify.com",
        "overcast.fm",
        "pocketcasts.com",
    }
)


def _domain_matches(domain: str, known_hosts: frozenset[str]) -> bool:
    """Return True if the domain exactly matches or is a subdomain of any
    host in known_hosts. Case-insensitive."""
    domain = domain.lower().strip()
    if not domain:
        return False
    return any(domain == host or domain.endswith("." + host) for host in known_hosts)


# Heuristic classifier from domain to SourceKind. Mirrors the Wayback adapter's
# intuition but errs more toward "gov" since direct is typically preferred for
# government sources.
def _source_kind_from_domain(domain: str) -> str:
    domain = domain.lower()
    if domain.endswith(".gov") or domain.endswith(".mil"):
        return "gov"
    if domain.endswith(".edu"):
        return "academic"
    if _domain_matches(domain, _PODCAST_HOSTS):
        return "podcast"
    if _domain_matches(domain, _SOCIAL_HOSTS):
        return "social"
    return "news"


def fetch_url(url: str) -> bytes:
    """Fetch a URL directly. Raises on non-200 responses."""
    with httpx.Client(
        headers=DEFAULT_HEADERS,
        timeout=60.0,
        follow_redirects=True,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def ingest_url(
    *,
    url: str,
    corpus_version: str,
    source_kind: str | None = None,
) -> IngestResult:
    """Ingest a single URL via direct HTTP fetch.

    1. Fetch the raw bytes from the live URL.
    2. Hand off to ``store_and_index`` for the shared extract + blob + upsert +
       document-insert tail.

    ``source_kind`` is an optional override. When None, it is inferred from
    the domain.
    """
    raw_bytes = fetch_url(url)
    domain = urlparse(url).netloc.lower()

    fetch = FetchResult(
        raw_bytes=raw_bytes,
        url=url,
        domain=domain,
        source_name=source_name_from_domain(domain),
        source_kind=source_kind or _source_kind_from_domain(domain),
        canonical_url=None,  # direct fetch: the URL itself is canonical
    )

    return store_and_index(
        fetch,
        corpus_version=corpus_version,
        adapter_name="direct",
    )
