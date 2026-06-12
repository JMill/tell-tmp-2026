"""Regression tests for SIG (compute_independence) metadata propagation.

The bug these guard against: non-default narrative corpora (e.g. the 2023
high-altitude objects set) used to render with slug fallbacks for
`narrative_label` and the literal string "Unknown" for `origin_label`,
because compute_independence read from NJ-drones-specific hardcoded maps
instead of from the loaded narrative_defs themselves.

These tests exercise the fix: when a narrative_def carries `label` and
`originating_source` fields (as loaded by load_narrative_defs from
narratives.yaml), compute_independence must return those values verbatim.

Run with: uv run pytest python/signals_methods/tests/test_independence_metadata.py
"""

from __future__ import annotations

from datetime import UTC, datetime

from signals_methods.independence import compute_independence
from signals_methods.nvd import NvdDocument


def _doc(doc_id: str, title: str, url: str) -> NvdDocument:
    return NvdDocument(
        document_id=doc_id,
        published_at=datetime(2023, 2, 3, 12, 0, tzinfo=UTC),
        title=title,
        url=url,
    )


def test_compute_independence_uses_label_and_origin_from_defs() -> None:
    """When the narrative_def carries label and originating_source, the SIG
    result must expose those values on narrative_label and origin_label."""
    docs = [
        _doc("1", "PRC spy balloon shot down over Atlantic", "https://example.com/a"),
        _doc(
            "2", "Pentagon confirms surveillance balloon attribution", "https://news.example.com/b"
        ),
    ]
    custom_defs = [
        {
            "slug": "prc-surveillance",
            "keywords": ["spy balloon", "surveillance balloon"],
            "label": "PRC PLA Surveillance Program",
            "originating_source": "DoD press briefing (Brig. Gen. Pat Ryder), February 2 2023",
        }
    ]

    results = compute_independence(docs, narrative_defs=custom_defs)
    assert len(results) == 1
    assert results[0].narrative_slug == "prc-surveillance"
    assert results[0].narrative_label == "PRC PLA Surveillance Program"
    assert results[0].origin_label.startswith("DoD press briefing")


def test_compute_independence_falls_back_to_slug_when_label_missing() -> None:
    """If a narrative_def omits `label`, the slug is the safe fallback."""
    docs = [_doc("1", "some content", "https://example.com/a")]
    defs = [{"slug": "custom-narrative", "keywords": ["content"]}]

    results = compute_independence(docs, narrative_defs=defs)
    assert results[0].narrative_label == "custom-narrative"


def test_compute_independence_falls_back_to_nj_map_for_known_slug() -> None:
    """For an NJ-drones slug without an explicit originating_source, the
    legacy hardcoded map still populates the origin label. This preserves
    backward compatibility for any caller that constructs narrative_defs
    without the rich metadata."""
    docs = [_doc("1", "Iranian mothership rumors circulate", "https://example.com/a")]
    defs = [{"slug": "iranian-mothership", "keywords": ["mothership", "iranian"]}]

    results = compute_independence(docs, narrative_defs=defs)
    assert results[0].origin_label == "Rep. Jeff Van Drew (R-NJ)"


def test_compute_independence_origin_unknown_for_unknown_slug_without_source() -> None:
    """An unknown slug with no originating_source in the def gracefully
    renders as 'Unknown' (pre-existing behavior preserved)."""
    docs = [_doc("1", "some content", "https://example.com/a")]
    defs = [{"slug": "brand-new-narrative", "keywords": ["content"]}]

    results = compute_independence(docs, narrative_defs=defs)
    assert results[0].origin_label == "Unknown"
