"""Sensemaking Quality Metrics (SQM) evaluation.

Computes evaluation metrics that connect the three signal methods (IVI, NVD,
SIG) back to the ground-truth timeline and the abstract's empirical claims.
Four metrics, each answering a different question about sensemaking quality:

1. **Contradicting evidence lag.** For each narrative-claim event in the
   timeline, how quickly does a corpus document appear that contradicts the
   claim? A document "contradicts" narrative N if it keyword-matches the
   narrative (it references the topic) but scores below the evidence threshold
   on N's supporting hypothesis (it discusses but does not support the claim).

2. **Composite narrative-capture risk.** For each day, do all three signals
   converge on the same narrative? High IVI (vacuum), high NVD (narrative
   outpacing evidence), and low independence score (echo chamber) on the same
   day for the same narrative is the structural signature of narrative capture.

3. **Evidence-narrative alignment.** Rank correlation between narrative volume
   and evidence support per time window. Low alignment means the loudest
   narrative is not the best-supported one.

4. **Premature closure resistance.** Entropy in the hypothesis distribution
   stays above a floor until the ground-truth timeline provides a resolution
   event.

No database dependency. I/O handled by storage.py and the CLI layer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml

from .constants import (
    CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
    CAPTURE_RISK_IVI_THRESHOLD,
    CAPTURE_RISK_NVD_THRESHOLD,
    EVIDENCE_THRESHOLD,
    NARRATIVE_DEFS,
)
from .nvd import (
    HypothesisScore,
    NvdDocument,
    NvdPoint,
    _matches_narrative,
)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TimelineEvent:
    """A single event from the ground-truth timeline.

    The SQM evaluator is case-study-agnostic: any timeline YAML that
    provides ``id``, ``date``, ``title``, ``category``, ``narratives``,
    and ``evidence_weight`` for each event is a valid input. Categories
    used by the contradicting-evidence-lag metric are ``observation`` and
    ``narrative-claim``; other categories are preserved but ignored.
    """

    id: str
    date: date
    title: str
    category: str  # observation | narrative-claim | etc.
    narratives: list[str]  # narrative slugs
    evidence_weight: str  # strong | moderate | weak | rumor


def load_timeline_from_yaml(yaml_path: str | Path) -> list[TimelineEvent]:
    """Load a ground-truth timeline from a YAML file.

    The YAML must contain an ``events`` list where each entry has ``id``,
    ``date`` (ISO 8601 string or YAML date), ``title``, ``category``, and
    optionally ``narratives`` and ``evidence_weight``. This schema is the
    reusable contract for case-study validation; the NJ-drones timeline
    is one instance, the 2023-balloon retrospective will be another, and
    so on.
    """
    path = Path(yaml_path)
    with open(path) as f:
        data = yaml.safe_load(f)

    events: list[TimelineEvent] = []
    for e in data.get("events", []):
        d = e["date"]
        if isinstance(d, str):
            d = date.fromisoformat(d)
        elif isinstance(d, datetime):
            # PyYAML parses YYYY-MM-DDTHH:MM as datetime; normalize to date.
            d = d.date()
        events.append(
            TimelineEvent(
                id=e["id"],
                date=d,
                title=e["title"],
                category=e["category"],
                narratives=e.get("narratives", []),
                evidence_weight=e.get("evidence_weight", "unknown"),
            )
        )
    return events


@dataclass(frozen=True)
class ContradictingEvidenceResult:
    """Lag measurement for a single narrative-claim event."""

    event_id: str
    event_date: date
    narrative_slug: str
    first_contradicting_doc_id: str | None
    first_contradicting_date: date | None
    lag_hours: float | None  # None if no contradicting doc found
    contradicting_doc_title: str | None
    contradicting_doc_score: float | None  # score on the supporting hypothesis


@dataclass(frozen=True)
class CaptureRiskAlert:
    """A day when all three signals converge on a narrative."""

    alert_date: date
    narrative_slug: str
    ivi_value: float
    nvd_value: float
    independence_score: float
    amplification_ratio: float
    risk_score: float  # composite


@dataclass(frozen=True)
class IviPoint:
    """A single IVI observation for one day."""

    window_end: date
    ivi_value: float


@dataclass(frozen=True)
class IndependenceResult:
    """Per-narrative independence score (from SIG)."""

    narrative_slug: str
    independence_score: float
    amplification_ratio: float


@dataclass(frozen=True)
class AlignmentResult:
    """Evidence-narrative alignment for one time window."""

    window_date: date
    rank_correlation: float  # Spearman rho: volume rank vs. evidence rank
    loudest_narrative: str
    best_supported_narrative: str
    aligned: bool  # loudest == best-supported


@dataclass(frozen=True)
class ClosureResistanceResult:
    """Premature closure resistance for one day."""

    day: date
    entropy_bits: float
    max_entropy_bits: float
    resistance_ratio: float  # entropy / max_entropy


# ---------------------------------------------------------------------------
# 1. Contradicting evidence lag
# ---------------------------------------------------------------------------


def compute_contradicting_evidence_lag(
    timeline_events: Sequence[TimelineEvent],
    documents: Sequence[NvdDocument],
    hypothesis_scores: Sequence[HypothesisScore],
    *,
    narrative_defs: list[dict[str, object]] | None = None,
    evidence_threshold: float = EVIDENCE_THRESHOLD,
) -> list[ContradictingEvidenceResult]:
    """For each narrative-claim event, find the first contradicting document.

    A document "contradicts" narrative N if:
    1. It keyword-matches N (it references the topic)
    2. Its score on N's supporting hypothesis is BELOW evidence_threshold
       (it discusses the narrative but does not support the underlying claim)
    3. It was published on or after the event date

    This captures documents like the Pentagon denial of the Iranian Mothership:
    the denial references "Iran" and "mothership" (matching keywords) but its
    H4 score is low because it refutes the claim.
    """
    ndefs = narrative_defs if narrative_defs is not None else NARRATIVE_DEFS
    defs_by_slug = {d["slug"]: d for d in ndefs}

    # Index scores by document_id
    scores_by_doc: dict[str, dict[str, float]] = {}
    for hs in hypothesis_scores:
        scores_by_doc.setdefault(hs.document_id, {})[hs.hypothesis_id] = hs.score

    # Filter to narrative-claim events
    claim_events = [e for e in timeline_events if e.category == "narrative-claim"]

    results: list[ContradictingEvidenceResult] = []

    for event in claim_events:
        for narrative_slug in event.narratives:
            ndef = defs_by_slug.get(narrative_slug)
            if ndef is None:
                continue

            keywords = ndef.get("keywords", [])
            hypothesis = str(ndef.get("hypothesis", ""))
            if not keywords or not hypothesis:
                continue

            # Find documents that keyword-match the narrative and were published
            # on or after the event date
            matching_docs = [
                doc
                for doc in documents
                if _matches_narrative(doc, keywords) and _to_date(doc.published_at) >= event.date
            ]

            # Among matching docs, find those whose hypothesis score is below
            # the evidence threshold (they discuss but don't support the claim).
            # Skip documents with no score for this hypothesis; treating
            # missing scores as 0.0 would falsely count unscored documents as
            # contradictions.
            contradicting: list[tuple[NvdDocument, float]] = []
            for doc in matching_docs:
                doc_scores = scores_by_doc.get(doc.document_id, {})
                if hypothesis not in doc_scores:
                    continue
                h_score = doc_scores[hypothesis]
                if h_score < evidence_threshold:
                    contradicting.append((doc, h_score))

            # Sort by date, then pick the earliest
            contradicting.sort(key=lambda x: x[0].published_at)

            if contradicting:
                first_doc, first_score = contradicting[0]
                first_date = _to_date(first_doc.published_at)
                # Compute lag in hours (date-level resolution = multiples of 24)
                lag_days = (first_date - event.date).days
                lag_hours = float(lag_days * 24)
                results.append(
                    ContradictingEvidenceResult(
                        event_id=event.id,
                        event_date=event.date,
                        narrative_slug=narrative_slug,
                        first_contradicting_doc_id=first_doc.document_id,
                        first_contradicting_date=first_date,
                        lag_hours=lag_hours,
                        contradicting_doc_title=first_doc.title,
                        contradicting_doc_score=first_score,
                    )
                )
            else:
                results.append(
                    ContradictingEvidenceResult(
                        event_id=event.id,
                        event_date=event.date,
                        narrative_slug=narrative_slug,
                        first_contradicting_doc_id=None,
                        first_contradicting_date=None,
                        lag_hours=None,
                        contradicting_doc_title=None,
                        contradicting_doc_score=None,
                    )
                )

    return results


# ---------------------------------------------------------------------------
# 2. Composite narrative-capture risk
# ---------------------------------------------------------------------------


def compute_capture_risk(
    ivi_series: Sequence[IviPoint],
    nvd_series: Sequence[NvdPoint],
    independence_results: Sequence[IndependenceResult],
    *,
    ivi_threshold: float = CAPTURE_RISK_IVI_THRESHOLD,
    nvd_threshold: float = CAPTURE_RISK_NVD_THRESHOLD,
    independence_threshold: float = CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
) -> list[CaptureRiskAlert]:
    """Flag days when IVI, NVD, and SIG converge on the same narrative.

    A narrative-capture-risk alert fires on day D for narrative N when:
    1. IVI on day D >= ivi_threshold (information vacuum exists)
    2. NVD for narrative N on day D >= nvd_threshold (narrative outpacing evidence)
    3. Independence score for narrative N <= independence_threshold (echo chamber)

    The risk_score is a product: (IVI / threshold) * (NVD / threshold) *
    (threshold / independence_score). Higher is worse.
    """
    # Index independence by narrative slug
    indep_by_slug: dict[str, IndependenceResult] = {
        r.narrative_slug: r for r in independence_results
    }

    # Index IVI by date
    ivi_by_date: dict[date, float] = {p.window_end: p.ivi_value for p in ivi_series}

    # Group NVD by (date, narrative)
    # Always normalize to date via _to_date(): datetime is a subclass of
    # date, so isinstance(dt, date) is True for datetimes, which would skip
    # the conversion and cause dict-key misses against the date-keyed IVI map.
    nvd_by_date_narrative: dict[tuple[date, str], NvdPoint] = {}
    for p in nvd_series:
        d = _to_date(p.window_end) if isinstance(p.window_end, datetime) else p.window_end
        nvd_by_date_narrative[(d, p.narrative_slug)] = p

    alerts: list[CaptureRiskAlert] = []

    # Check each NVD point
    for (d, slug), nvd_point in nvd_by_date_narrative.items():
        if nvd_point.nvd_value < nvd_threshold:
            continue

        ivi_val = ivi_by_date.get(d)
        if ivi_val is None or ivi_val < ivi_threshold:
            continue

        indep = indep_by_slug.get(slug)
        if indep is None or indep.independence_score > independence_threshold:
            continue

        # All three conditions met
        risk = (
            (ivi_val / ivi_threshold)
            * (nvd_point.nvd_value / nvd_threshold)
            * (independence_threshold / indep.independence_score)
        )

        alerts.append(
            CaptureRiskAlert(
                alert_date=d,
                narrative_slug=slug,
                ivi_value=ivi_val,
                nvd_value=nvd_point.nvd_value,
                independence_score=indep.independence_score,
                amplification_ratio=indep.amplification_ratio,
                risk_score=round(risk, 2),
            )
        )

    alerts.sort(key=lambda a: (a.alert_date, a.narrative_slug))
    return alerts


# ---------------------------------------------------------------------------
# 3. Evidence-narrative alignment
# ---------------------------------------------------------------------------


def compute_alignment(
    documents: Sequence[NvdDocument],
    hypothesis_scores: Sequence[HypothesisScore],
    *,
    narrative_defs: list[dict[str, object]] | None = None,
    evidence_threshold: float = EVIDENCE_THRESHOLD,
    window_days: int = 3,
) -> list[AlignmentResult]:
    """Compute rank correlation between narrative volume and evidence support.

    For each rolling window, rank narratives by document volume and by
    evidence support (count of docs scoring above threshold). Compute
    whether the loudest narrative is also the best-supported.
    """
    ndefs = narrative_defs if narrative_defs is not None else NARRATIVE_DEFS

    scores_by_doc: dict[str, dict[str, float]] = {}
    for hs in hypothesis_scores:
        scores_by_doc.setdefault(hs.document_id, {})[hs.hypothesis_id] = hs.score

    def _date(dt: datetime) -> date:
        if dt.tzinfo is None:
            return dt.date()
        return dt.astimezone(UTC).date()

    doc_dates = {doc.document_id: _date(doc.published_at) for doc in documents}
    if not doc_dates:
        return []

    series_start = min(doc_dates.values())
    series_end = max(doc_dates.values())

    results: list[AlignmentResult] = []
    d = series_start
    while d <= series_end:
        ws = d - timedelta(days=window_days - 1)

        # Docs in this window
        window_docs = [
            doc for doc in documents if ws <= doc_dates.get(doc.document_id, series_start) <= d
        ]

        if not window_docs:
            d += timedelta(days=1)
            continue

        # Count volume and evidence per narrative
        volume: dict[str, int] = {}
        evidence: dict[str, int] = {}
        for ndef in ndefs:
            slug = str(ndef["slug"])
            keywords = ndef.get("keywords", [])
            hypothesis = str(ndef.get("hypothesis", ""))

            matched = [doc for doc in window_docs if _matches_narrative(doc, keywords)]
            volume[slug] = len(matched)

            ev_count = 0
            for doc in matched:
                doc_scores = scores_by_doc.get(doc.document_id, {})
                if doc_scores.get(hypothesis, 0.0) >= evidence_threshold:
                    ev_count += 1
            evidence[slug] = ev_count

        # Find loudest and best-supported (among narratives with >0 volume)
        active = {s: v for s, v in volume.items() if v > 0}
        if not active:
            d += timedelta(days=1)
            continue

        loudest = max(active, key=lambda s: active[s])
        active_evidence = {s: evidence.get(s, 0) for s in active}
        best_supported = max(active_evidence, key=lambda s: active_evidence[s])

        # Simple Spearman-like rank correlation (manual, no scipy dependency)
        slugs = sorted(active.keys())
        n = len(slugs)
        if n < 2:
            rho = 1.0
        else:
            vol_ranked = _rank_values([active[s] for s in slugs])
            ev_ranked = _rank_values([active_evidence[s] for s in slugs])
            d_sq = sum((v - e) ** 2 for v, e in zip(vol_ranked, ev_ranked, strict=True))
            rho = 1 - (6 * d_sq) / (n * (n**2 - 1))

        results.append(
            AlignmentResult(
                window_date=d,
                rank_correlation=round(rho, 3),
                loudest_narrative=loudest,
                best_supported_narrative=best_supported,
                aligned=loudest == best_supported,
            )
        )

        d += timedelta(days=1)

    return results


# ---------------------------------------------------------------------------
# 4. Premature closure resistance
# ---------------------------------------------------------------------------


def compute_closure_resistance(
    daily_distributions: Sequence[dict],
) -> list[ClosureResistanceResult]:
    """Compute entropy-based closure resistance from daily hypothesis distributions.

    Input: list of dicts with keys {day, entropy_bits, ...} as returned
    by load_daily_distributions() in storage.py.
    """
    from .constants import MAX_ENTROPY_BITS

    max_entropy = MAX_ENTROPY_BITS

    results: list[ClosureResistanceResult] = []
    for dist in daily_distributions:
        day = dist["day"]
        if isinstance(day, str):
            day = date.fromisoformat(day)

        entropy = float(dist.get("entropy_bits", 0.0))
        results.append(
            ClosureResistanceResult(
                day=day,
                entropy_bits=round(entropy, 3),
                max_entropy_bits=round(max_entropy, 3),
                resistance_ratio=round(entropy / max_entropy, 3) if max_entropy > 0 else 0.0,
            )
        )

    results.sort(key=lambda r: r.day)
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_date(dt: datetime) -> date:
    """Convert datetime to UTC date."""
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(UTC).date()


def _rank_values(values: list[int | float]) -> list[float]:
    """Assign fractional ranks to a list of values (ties get average rank)."""
    n = len(values)
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j - 1) / 2.0 + 1  # 1-based
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks
