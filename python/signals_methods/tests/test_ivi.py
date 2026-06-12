"""Unit tests for the Information Vacuum Index method.

These are pure-function tests — no database, no network. Synthetic
DocumentRecord fixtures cover: empty corpus, single day, rolling window
math, discourse/authoritative partition, Laplace smoothing, and the
ordering of the output time series.

Run with: uv run pytest python/signals_methods/tests/test_ivi.py
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from signals_methods.ivi import (
    AUTHORITATIVE_SOURCE_KINDS,
    DEFAULT_WINDOW_DAYS,
    DISCOURSE_SOURCE_KINDS,
    LAPLACE_SMOOTHER,
    DocumentRecord,
    compute_ivi,
)


def _doc(pub: date | datetime, kind: str) -> DocumentRecord:
    if isinstance(pub, date) and not isinstance(pub, datetime):
        pub = datetime.combine(pub, datetime.min.time(), tzinfo=UTC)
    return DocumentRecord(published_at=pub, source_kind=kind)


def test_partition_constants_are_disjoint() -> None:
    """Regression guard against future editors putting a source kind in both
    partitions, which would double-count."""
    assert DISCOURSE_SOURCE_KINDS.isdisjoint(AUTHORITATIVE_SOURCE_KINDS)


def test_default_window_is_seven_days() -> None:
    assert DEFAULT_WINDOW_DAYS == 7


def test_empty_corpus_requires_explicit_range() -> None:
    with pytest.raises(ValueError, match="non-empty document list"):
        compute_ivi([])


def test_invalid_window_days_raises() -> None:
    doc = _doc(date(2024, 12, 11), "news")
    with pytest.raises(ValueError, match="window_days must be >= 1"):
        compute_ivi([doc], window_days=0)


def test_single_discourse_doc_window_of_1() -> None:
    """One discourse doc on day X, window_days=1. IVI = 1 / (0 + 1) = 1.0."""
    doc = _doc(date(2024, 12, 11), "news")
    results = compute_ivi([doc], window_days=1)
    assert len(results) == 1
    r = results[0]
    assert r.discourse_count == 1
    assert r.authoritative_count == 0
    assert r.value == 1.0
    assert r.window_end.date() == date(2024, 12, 11)


def test_equal_discourse_and_authoritative() -> None:
    """Two discourse, two authoritative same day. IVI = 2 / (2 + 1) = 0.667."""
    docs = [
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 11), "gov"),
        _doc(date(2024, 12, 11), "gov"),
    ]
    results = compute_ivi(docs, window_days=1)
    assert len(results) == 1
    assert results[0].discourse_count == 2
    assert results[0].authoritative_count == 2
    assert results[0].value == pytest.approx(2 / 3)


def test_laplace_smoother_prevents_divide_by_zero() -> None:
    """High discourse, zero authoritative. IVI = 10 / (0 + 1) = 10."""
    docs = [_doc(date(2024, 12, 11), "news") for _ in range(10)]
    results = compute_ivi(docs, window_days=1)
    assert results[0].value == 10.0
    assert LAPLACE_SMOOTHER == 1


def test_rolling_window_sums_over_preceding_days() -> None:
    """A 7-day rolling window ending on day X includes days X-6 through X."""
    docs = [
        _doc(date(2024, 12, 5), "news"),
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 11), "gov"),
    ]
    results = compute_ivi(docs, window_days=7)
    # Find the window ending on Dec 11
    dec11 = next(r for r in results if r.window_end.date() == date(2024, 12, 11))
    # Window is Dec 5-11 (7 days inclusive). Contains all 4 docs.
    assert dec11.discourse_count == 3
    assert dec11.authoritative_count == 1
    assert dec11.value == pytest.approx(3 / 2)

    # A window ending on Dec 4 is before all docs. Should be IVI = 0/1 = 0.
    dec4 = next(
        (r for r in results if r.window_end.date() == date(2024, 12, 4)),
        None,
    )
    # Only exists if range_start allows it. By default range_start is the
    # earliest doc date (Dec 5), so Dec 4 is not in the range.
    assert dec4 is None
    # Dec 5 window (Nov 29 - Dec 5) should have just the one discourse doc.
    dec5 = next(r for r in results if r.window_end.date() == date(2024, 12, 5))
    assert dec5.discourse_count == 1
    assert dec5.authoritative_count == 0


def test_explicit_range_extends_series() -> None:
    """Passing range_start and range_end produces a row for every day in that
    range even if the corpus has no documents on that day."""
    docs = [_doc(date(2024, 12, 11), "news")]
    results = compute_ivi(
        docs,
        window_days=1,
        range_start=date(2024, 12, 8),
        range_end=date(2024, 12, 14),
    )
    assert len(results) == 7  # Dec 8 through Dec 14 inclusive
    # Only Dec 11 has content
    for r in results:
        if r.window_end.date() == date(2024, 12, 11):
            assert r.discourse_count == 1
            assert r.value == 1.0
        else:
            assert r.discourse_count == 0
            assert r.value == 0.0


def test_unknown_source_kinds_are_ignored() -> None:
    """Documents with a source_kind outside both partitions do not contribute."""
    docs = [
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 11), "other"),  # not discourse, not authoritative
        _doc(date(2024, 12, 11), "weird"),  # not in any partition
    ]
    results = compute_ivi(docs, window_days=1)
    assert results[0].discourse_count == 1
    assert results[0].authoritative_count == 0


def test_results_are_sorted_by_window_end() -> None:
    docs = [
        _doc(date(2024, 12, 11), "news"),
        _doc(date(2024, 12, 5), "news"),
        _doc(date(2024, 12, 8), "gov"),
    ]
    results = compute_ivi(docs, window_days=1)
    ends = [r.window_end for r in results]
    assert ends == sorted(ends)


def test_all_source_kinds_classify_correctly() -> None:
    """Every source kind in the CU26 framework has a home in exactly one
    partition (or none, if it's 'other')."""
    assert "news" in DISCOURSE_SOURCE_KINDS
    assert "social" in DISCOURSE_SOURCE_KINDS
    assert "forum" in DISCOURSE_SOURCE_KINDS
    assert "podcast" in DISCOURSE_SOURCE_KINDS
    assert "gov" in AUTHORITATIVE_SOURCE_KINDS
    assert "academic" in AUTHORITATIVE_SOURCE_KINDS
    assert "aviation" in AUTHORITATIVE_SOURCE_KINDS
    # 'other' should be in neither
    assert "other" not in DISCOURSE_SOURCE_KINDS
    assert "other" not in AUTHORITATIVE_SOURCE_KINDS


def test_window_end_is_end_of_day() -> None:
    """Window end datetimes should be set to end-of-day (23:59:59) so they
    compare cleanly against tz-aware timestamps elsewhere."""
    docs = [_doc(date(2024, 12, 11), "news")]
    r = compute_ivi(docs, window_days=1)[0]
    assert r.window_end.hour == 23
    assert r.window_end.minute == 59
    assert r.window_end.tzinfo == UTC


def test_realistic_nj_drones_shape() -> None:
    """Realistic micro-corpus that mirrors the actual NJ drones distribution.
    Peak window should be around Dec 11-17 when the Iranian Mothership
    narrative burst happened with minimal institutional response."""
    docs = []
    # Pre-peak: 1 doc per week
    docs.append(_doc(date(2024, 11, 21), "news"))
    docs.append(_doc(date(2024, 12, 3), "gov"))  # FBI opens investigation
    # Peak week: narrative burst
    docs.extend([_doc(date(2024, 12, 11), "news") for _ in range(6)])
    docs.append(_doc(date(2024, 12, 12), "gov"))  # Joint DHS/FBI statement
    docs.extend([_doc(date(2024, 12, 13), "news") for _ in range(2)])
    docs.extend([_doc(date(2024, 12, 16), "news") for _ in range(4)])
    docs.append(_doc(date(2024, 12, 16), "podcast"))
    docs.extend([_doc(date(2024, 12, 18), "news") for _ in range(3)])

    results = compute_ivi(docs, window_days=7)
    peak = max(results, key=lambda r: r.value)
    # Peak should be somewhere in the Dec 11-20 range
    assert date(2024, 12, 11) <= peak.window_end.date() <= date(2024, 12, 20), (
        f"Peak window at {peak.window_end.date()} is outside the expected Dec 11-20 vacuum window"
    )
    # Peak IVI should be > 3 given the discourse/authoritative imbalance
    assert peak.value > 3.0, f"Peak IVI {peak.value:.2f} is unexpectedly low"
