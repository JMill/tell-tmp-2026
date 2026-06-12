"""Information Vacuum Index (IVI).

Quantifies the gap between public discourse volume and authoritative
institutional response on a topic, computed over a rolling time window.

Formal definition:

    IVI(topic, t, w) = discourse_volume(topic, [t-w, t])
                       --------------------------------
                       authoritative_response(topic, [t-w, t]) + 1

Where:
- `discourse_volume` counts documents from non-authoritative source kinds
  (news, social, forum, podcast) published in the window
- `authoritative_response` counts documents from authoritative source
  kinds (gov, academic, aviation) published in the same window
- The `+ 1` in the denominator is a Laplace smoother that keeps IVI
  finite when there is no institutional response and bounds it to a
  scale comparable across windows. See Design notes below for why this
  is preferred to the naïve `+ ε`.
- `w` is the window length in days (default 7).

High IVI means the discourse is expanding rapidly without a corresponding
institutional response, the structural condition the Lawfare piece
"The Disclosure Trap" describes as vulnerable to narrative capture.

## Design notes

1. **Laplace smoothing (+1) beats +ε.** A tiny epsilon like 1e-6 makes
   IVI blow up as authoritative response goes to zero, producing
   enormous values that obscure the meaningful dynamic range. Using +1
   keeps IVI intuitive: a window with 10 discourse docs and 0 gov docs
   has IVI = 10/1 = 10, and a window with 10 discourse docs and 2 gov
   docs has IVI = 10/3 ≈ 3.3. The ratio still captures the vacuum
   signal and the numbers stay human-readable.

2. **Rolling windows by default.** For small corpora the ratio is
   unstable day-to-day, so we default to 7-day rolling windows. The
   caller can override to 1-day (raw daily), 14-day (smoother), or
   any other integer.

3. **Window anchored to the right edge.** Each IVI value is attributed
   to the window's END timestamp, not its midpoint. This makes the
   time series interpretable as "IVI as of day X, measured over the
   preceding w days", matching how a real-time deployment would work.

4. **Source kinds partitioned statically.** The discourse / authoritative
   partition is hard-coded in this module. A production deployment
   might want to make this configurable per topic. For Phase B it is
   deliberately fixed to match the definition in the method doc at
   docs/methods/ivi.md.

5. **This module has no database dependency.** It operates on an
   iterable of `DocumentRecord` tuples. The caller is responsible for
   loading documents from whatever source (Neon, a parquet file, an
   in-memory fixture) and passing them in. This keeps the method unit-
   testable without any database and keeps the computation reusable
   across storage backends.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from signals_methods.constants import (
    AUTHORITATIVE_SOURCE_KINDS,
    DISCOURSE_SOURCE_KINDS,
    LAPLACE_SMOOTHER,
)
from signals_methods.constants import (
    IVI_DEFAULT_WINDOW_DAYS as DEFAULT_WINDOW_DAYS,
)


@dataclass(frozen=True)
class DocumentRecord:
    """Minimal document tuple the IVI method needs.

    This is deliberately a simple dataclass rather than a full pydantic
    Document so that the method has no dependency on signals_core and can
    be exercised against synthetic fixtures in tests.
    """

    published_at: datetime
    source_kind: str


@dataclass(frozen=True)
class IviResult:
    """One row of the IVI time series."""

    window_start: datetime
    window_end: datetime
    discourse_count: int
    authoritative_count: int
    value: float

    def as_dict(self) -> dict[str, object]:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "discourse_count": self.discourse_count,
            "authoritative_count": self.authoritative_count,
            "value": round(self.value, 4),
        }


def compute_ivi(
    documents: Iterable[DocumentRecord],
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    range_start: date | None = None,
    range_end: date | None = None,
) -> list[IviResult]:
    """Compute the IVI time series for a sequence of documents.

    Args:
        documents: iterable of DocumentRecord tuples, one per document in
            the topic corpus. Only published_at and source_kind are used.
            Documents with source_kind that falls outside both the
            discourse and authoritative partitions are ignored (logged
            upstream, not here).
        window_days: width of the rolling window in days. Default 7.
        range_start: optional inclusive lower bound for the output series.
            If None, derived from the earliest document in the corpus.
        range_end: optional inclusive upper bound for the output series.
            If None, derived from the latest document in the corpus.

    Returns:
        List of IviResult values, one per day in [range_start, range_end],
        sorted by window_end ascending.

    Raises:
        ValueError if window_days < 1 or if documents is empty and no
            explicit range is supplied.
    """
    if window_days < 1:
        raise ValueError(f"window_days must be >= 1, got {window_days}")

    # Materialize so we can iterate multiple times.
    doc_list = list(documents)

    if range_start is None or range_end is None:
        if not doc_list:
            raise ValueError(
                "compute_ivi needs either a non-empty document list or "
                "explicit range_start and range_end"
            )
        published_dates = [d.published_at.date() for d in doc_list]
        if range_start is None:
            range_start = min(published_dates)
        if range_end is None:
            range_end = max(published_dates)

    assert range_start is not None and range_end is not None
    if range_start > range_end:
        raise ValueError(f"range_start ({range_start}) must be <= range_end ({range_end})")

    # Bucket documents by calendar day (UTC) so window sums are O(range) and
    # not O(range * docs). Day keys are naive dates; we only care about UTC
    # calendar boundaries.
    discourse_per_day: dict[date, int] = {}
    authoritative_per_day: dict[date, int] = {}
    for doc in doc_list:
        pub_date = doc.published_at.astimezone(UTC).date()
        if doc.source_kind in DISCOURSE_SOURCE_KINDS:
            discourse_per_day[pub_date] = discourse_per_day.get(pub_date, 0) + 1
        elif doc.source_kind in AUTHORITATIVE_SOURCE_KINDS:
            authoritative_per_day[pub_date] = authoritative_per_day.get(pub_date, 0) + 1
        # else: unknown source kind, ignored

    results: list[IviResult] = []
    cursor = range_start
    window = timedelta(days=window_days - 1)  # inclusive bounds
    while cursor <= range_end:
        window_start_date = cursor - window
        window_end_date = cursor

        discourse = 0
        authoritative = 0
        day = window_start_date
        while day <= window_end_date:
            discourse += discourse_per_day.get(day, 0)
            authoritative += authoritative_per_day.get(day, 0)
            day += timedelta(days=1)

        value = discourse / (authoritative + LAPLACE_SMOOTHER)

        # Convert date bounds back to UTC datetimes (start of window at 00:00,
        # end of window at 23:59:59.999999) so the storage layer has a stable
        # tz-aware representation.
        window_start_dt = datetime.combine(window_start_date, datetime.min.time(), tzinfo=UTC)
        window_end_dt = datetime.combine(window_end_date, datetime.max.time(), tzinfo=UTC)

        results.append(
            IviResult(
                window_start=window_start_dt,
                window_end=window_end_dt,
                discourse_count=discourse,
                authoritative_count=authoritative,
                value=value,
            )
        )
        cursor += timedelta(days=1)

    return results
