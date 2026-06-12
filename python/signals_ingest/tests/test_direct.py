"""Unit tests for the direct adapter's pure functions.

Network-touching functions (fetch_url, ingest_url) are covered by the
smoke test instead.
"""

from __future__ import annotations

from signals_ingest.adapters.direct import (
    DEFAULT_HEADERS,
    _source_kind_from_domain,
)


def test_default_headers_has_accept() -> None:
    assert "Accept" in DEFAULT_HEADERS
    assert "text/html" in DEFAULT_HEADERS["Accept"]


def test_source_kind_from_gov_domain() -> None:
    assert _source_kind_from_domain("www.fbi.gov") == "gov"
    assert _source_kind_from_domain("dhs.gov") == "gov"
    assert _source_kind_from_domain("defense.gov") == "gov"


def test_source_kind_from_mil_domain() -> None:
    assert _source_kind_from_domain("picatinny.army.mil") == "gov"


def test_source_kind_from_edu_domain() -> None:
    assert _source_kind_from_domain("cmu.edu") == "academic"


def test_source_kind_from_social_domain() -> None:
    assert _source_kind_from_domain("www.reddit.com") == "social"
    assert _source_kind_from_domain("bsky.app") == "social"
    assert _source_kind_from_domain("twitter.com") == "social"
    assert _source_kind_from_domain("x.com") == "social"
    assert _source_kind_from_domain("www.x.com") == "social"


def test_source_kind_from_podcast_domain() -> None:
    assert _source_kind_from_domain("podcasts.apple.com") == "podcast"
    assert _source_kind_from_domain("open.spotify.com") == "podcast"


def test_source_kind_news_fallback() -> None:
    assert _source_kind_from_domain("www.nytimes.com") == "news"
    assert _source_kind_from_domain("some-random-blog.example") == "news"


def test_social_host_match_is_not_substring() -> None:
    """Regression test for the substring-match bug Codex flagged on PR #6.

    Previously `"x.com" in domain` would match any domain containing the
    substring "x.com", including fox.com and examplex.com. The classifier
    now uses exact-or-subdomain matching so those are correctly classified
    as news rather than social.
    """
    # These would have been false positives under the old substring logic.
    assert _source_kind_from_domain("fox.com") == "news"
    assert _source_kind_from_domain("www.fox.com") == "news"
    assert _source_kind_from_domain("examplex.com") == "news"
    assert _source_kind_from_domain("foxnews.com") == "news"
    # Domains that legitimately should match still do.
    assert _source_kind_from_domain("x.com") == "social"
    assert _source_kind_from_domain("api.x.com") == "social"


def test_podcast_host_match_is_not_substring() -> None:
    """Same substring-match bug applied to podcast classification. A domain
    like 'podcastfan.com' should NOT be classified as a podcast host; only
    known podcast platforms should."""
    # False positives under any loose substring rule.
    assert _source_kind_from_domain("podcastfan.com") == "news"
    assert _source_kind_from_domain("podcasting-news.com") == "news"
    assert _source_kind_from_domain("podcasts-for-life.com") == "news"
    # Legitimate podcast hosts still match.
    assert _source_kind_from_domain("podcasts.apple.com") == "podcast"
    assert _source_kind_from_domain("www.podcasts.apple.com") == "podcast"
