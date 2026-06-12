"""Narrative Velocity Divergence (NVD).

NVD measures when a narrative spreads faster than supporting evidence can
accumulate. A high NVD reading on a given day means the narrative is gaining
traction in discourse while the underlying documents that would corroborate it
are not appearing at a matching rate, the classic pattern of echo amplification
and premature narrative capture.

Algorithm
---------
For each pre-defined narrative N and each day D:

  narrative_velocity[N, D]  = number of corpus documents in the rolling window
                               ending on D that keyword-match narrative N.
  evidence_velocity[N, D]   = number of corpus documents in the same window
                               that hypothesis-score >= EVIDENCE_THRESHOLD on
                               the hypothesis linked to narrative N.
  nvd[N, D]                 = narrative_velocity / (evidence_velocity + 1)

A ratio of 1.0 means narrative spread and evidence growth are in step.
A ratio > 2.0 is a meaningful divergence signal. The Laplace +1 in the
denominator prevents division-by-zero and handles the realistic case where
zero corroborating documents appear in the window.

Narrative classification
------------------------
Documents are matched to narratives via keyword patterns derived from each
narrative's definition. Matching is case-insensitive and applied to the
document's title and URL. A document can match multiple narratives.

This is intentionally simple. At 38 documents, ML clustering would overfit.
Expert-curated keyword patterns are more defensible and interpretable.

Evidence classification
-----------------------
A document is counted as "evidence" for narrative N if its hypothesis score
for N's supporting hypothesis is >= EVIDENCE_THRESHOLD (default 0.35).
Hypothesis scores come from document_hypothesis_scores and must already
be computed (Phase C).

No database dependency in this module. I/O is handled by storage.py and
the CLI layer, enabling unit tests against in-memory fixtures.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from signals_methods.constants import (
    EVIDENCE_THRESHOLD,
    NARRATIVE_DEFS,
)
from signals_methods.constants import (
    NVD_DEFAULT_WINDOW_DAYS as DEFAULT_WINDOW_DAYS,
)

# Re-export for backward compatibility (eval.py, independence.py import from here)
__all__ = [
    "DEFAULT_WINDOW_DAYS",
    "EVIDENCE_THRESHOLD",
    "NARRATIVE_DEFS",
    "HypothesisScore",
    "NvdDocument",
    "NvdPoint",
    "_matches_narrative",
    "compute_nvd",
]


@dataclass(frozen=True)
class NvdDocument:
    """A document record for NVD computation."""

    document_id: str
    published_at: datetime
    title: str
    url: str


@dataclass(frozen=True)
class HypothesisScore:
    """A single hypothesis score for a document."""

    document_id: str
    hypothesis_id: str  # H1..H5
    score: float


@dataclass(frozen=True)
class NvdPoint:
    """A single NVD observation for one narrative on one day."""

    narrative_slug: str
    window_start: datetime
    window_end: datetime
    narrative_velocity: int  # docs matching this narrative in the window
    evidence_velocity: int  # docs providing hypothesis-supported evidence
    nvd_value: float  # narrative_velocity / (evidence_velocity + 1)


def _matches_narrative(doc: NvdDocument, keywords: list[str]) -> bool:
    """Return True if any keyword appears in the document's title or URL."""
    haystack = (doc.title + " " + doc.url).lower()
    return any(kw.lower() in haystack for kw in keywords)


def _window_dates(
    series_start: date,
    series_end: date,
    window_days: int,
) -> list[tuple[date, date]]:
    """Yield (window_start, window_end) pairs covering the corpus date range."""
    windows = []
    d = series_start
    while d <= series_end:
        ws = d - timedelta(days=window_days - 1)
        windows.append((ws, d))
        d += timedelta(days=1)
    return windows


def compute_nvd(
    documents: Sequence[NvdDocument],
    hypothesis_scores: Sequence[HypothesisScore],
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    narrative_defs: list[dict[str, object]] | None = None,
    evidence_threshold: float = EVIDENCE_THRESHOLD,
) -> list[NvdPoint]:
    """Compute NVD for all narratives across the corpus date range.

    Raises ValueError if window_days <= 0.

    Parameters
    ----------
    documents:
        All corpus documents. Must have non-null published_at.
    hypothesis_scores:
        All H1-H5 scores for every document. Documents with no scores
        contribute zero evidence for every narrative.
    window_days:
        Rolling window width in calendar days.
    narrative_defs:
        Narrative definitions. Defaults to NARRATIVE_DEFS (from narratives.yaml).
        Override in unit tests to inject minimal fixtures.
    evidence_threshold:
        Minimum hypothesis score to count a document as evidence.

    Returns
    -------
    list[NvdPoint]
        One NvdPoint per (narrative, day), sorted by narrative slug then date.
    """
    if window_days <= 0:
        raise ValueError(f"window_days must be positive, got {window_days}")

    if not documents:
        return []

    ndefs = narrative_defs if narrative_defs is not None else NARRATIVE_DEFS

    # Index scores by document_id for O(1) lookup
    scores_by_doc: dict[str, dict[str, float]] = {}
    for hs in hypothesis_scores:
        scores_by_doc.setdefault(hs.document_id, {})[hs.hypothesis_id] = hs.score

    # Convert all dates to UTC date objects for bucketing
    def _date(dt: datetime) -> date:
        if dt.tzinfo is None:
            return dt.date()
        return dt.astimezone(UTC).date()

    doc_dates = {doc.document_id: _date(doc.published_at) for doc in documents}
    series_start = min(doc_dates.values())
    series_end = max(doc_dates.values())
    windows = _window_dates(series_start, series_end, window_days)

    results: list[NvdPoint] = []

    for ndef in ndefs:
        slug = str(ndef["slug"])
        hypothesis = str(ndef["hypothesis"])
        keywords = list(ndef["keywords"])  # type: ignore[arg-type]

        # Pre-classify documents for this narrative
        narrative_docs = {doc.document_id for doc in documents if _matches_narrative(doc, keywords)}

        # Pre-classify evidence documents (hypothesis score meets threshold)
        evidence_docs = {
            doc_id
            for doc_id, h_scores in scores_by_doc.items()
            if h_scores.get(hypothesis, 0.0) >= evidence_threshold
        }

        for ws, we in windows:
            # Documents published within the window
            in_window = {doc_id for doc_id, d in doc_dates.items() if ws <= d <= we}
            n_velocity = len(in_window & narrative_docs)
            e_velocity = len(in_window & evidence_docs)
            nvd_value = n_velocity / (e_velocity + 1)

            results.append(
                NvdPoint(
                    narrative_slug=slug,
                    window_start=datetime(ws.year, ws.month, ws.day, tzinfo=UTC),
                    window_end=datetime(we.year, we.month, we.day, tzinfo=UTC),
                    narrative_velocity=n_velocity,
                    evidence_velocity=e_velocity,
                    nvd_value=nvd_value,
                )
            )

    return sorted(results, key=lambda p: (p.narrative_slug, p.window_end))
