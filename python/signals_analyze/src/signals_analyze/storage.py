"""Storage helpers for signals_analyze.

Loads corpus documents (with their raw HTML content fetched on demand from
Vercel Blob) and persists hypothesis scores + aggregated distributions.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime

import psycopg
from signals_core import neon_connection
from vercel_blob_client import fetch as fetch_blob

from signals_analyze.hypothesis_scoring import HypothesisScores

__all__ = [
    "fetch_blob",
    # Plus the analyze-specific helpers defined below.
]


@dataclass(frozen=True)
class CorpusDocument:
    """A document loaded from the corpus, ready for hypothesis scoring."""

    id: str
    url: str
    title: str | None
    source_kind: str
    source_domain: str
    published_at: datetime | None
    content_blob_key: str | None
    content_hash: str
    corpus_version: str


def load_corpus_documents(
    corpus_version: str,
    limit: int | None = None,
) -> list[CorpusDocument]:
    """Load all documents in a corpus joined with source metadata."""
    sql = """
        SELECT d.id, d.url, d.title, d.published_at, d.content_blob_key,
               d.content_hash, d.corpus_version,
               s.kind AS source_kind, s.domain AS source_domain
        FROM documents d
        JOIN sources s ON s.id = d.source_id
        WHERE d.corpus_version = %s
        ORDER BY d.published_at ASC NULLS LAST, d.fetched_at ASC
    """
    params: list[object] = [corpus_version]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        CorpusDocument(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            source_kind=row["source_kind"],
            source_domain=row["source_domain"],
            published_at=row["published_at"],
            content_blob_key=row["content_blob_key"],
            content_hash=row["content_hash"],
            corpus_version=row["corpus_version"],
        )
        for row in rows
    ]


def upsert_hypothesis_scores(
    *,
    document_id: str,
    scores: HypothesisScores,
    model: str,
    prompt_version: str,
) -> int:
    """Insert or update the five rows for one document's H1-H5 scores.

    Idempotent on (document_id, hypothesis_id, prompt_version, model).
    Returns the number of rows affected (always 5 on success).
    """
    now = datetime.now(UTC)
    score_dict = scores.as_dict()
    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for hypothesis_id, score in score_dict.items():
            key = f"{document_id}|{hypothesis_id}|{prompt_version}|{model}".encode()
            row_id = "dhs_" + hashlib.sha1(key).hexdigest()[:24]
            cur.execute(
                """
                    INSERT INTO document_hypothesis_scores (
                        id, document_id, hypothesis_id, score, rationale,
                        model, prompt_version, scored_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, hypothesis_id, prompt_version, model)
                    DO UPDATE
                        SET score = EXCLUDED.score,
                            rationale = EXCLUDED.rationale,
                            scored_at = EXCLUDED.scored_at
                    """,
                (
                    row_id,
                    document_id,
                    hypothesis_id,
                    float(score),
                    scores.rationale,
                    model,
                    prompt_version,
                    now,
                ),
            )
            affected += 1
    return affected


def count_scored_documents(
    *,
    corpus_version: str,
    prompt_version: str,
    model: str,
) -> int:
    """How many documents in the corpus already have scores for this prompt+model.

    Used by the CLI to support resumable runs — skip documents that have
    already been scored.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT COUNT(DISTINCT d.id)::int AS n
                FROM documents d
                JOIN document_hypothesis_scores s ON s.document_id = d.id
                WHERE d.corpus_version = %s
                  AND s.prompt_version = %s
                  AND s.model = %s
                """,
            (corpus_version, prompt_version, model),
        )
        row = cur.fetchone()
        return row["n"] if row else 0


def get_scored_document_ids(
    *,
    corpus_version: str,
    prompt_version: str,
    model: str,
) -> set[str]:
    """Return the set of document ids in the corpus that already have scores
    for the given (prompt_version, model)."""
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT DISTINCT d.id
                FROM documents d
                JOIN document_hypothesis_scores s ON s.document_id = d.id
                WHERE d.corpus_version = %s
                  AND s.prompt_version = %s
                  AND s.model = %s
                """,
            (corpus_version, prompt_version, model),
        )
        rows = cur.fetchall()
    return {row["id"] for row in rows}


# ---------------------------------------------------------------------------
# Hypothesis distribution aggregation
# ---------------------------------------------------------------------------


def _shannon_entropy_bits(probs: list[float]) -> float:
    """Shannon entropy in bits over a probability distribution.

    The hypothesis scores are independent (do not sum to 1) so we first
    normalize. If all probabilities are zero, entropy is 0.
    """
    total = sum(probs)
    if total <= 0.0:
        return 0.0
    normalized = [p / total for p in probs]
    return -sum(p * math.log2(p) for p in normalized if p > 0.0)


@dataclass(frozen=True)
class DailyDistribution:
    day: date
    document_count: int
    distribution: dict[str, float]  # H1..H5 mean scores across docs that day
    entropy: float
    modal_hypothesis: str
    modal_probability: float


def aggregate_daily_distributions(
    *,
    corpus_version: str,
    prompt_version: str,
    model: str,
) -> list[DailyDistribution]:
    """Compute daily H1-H5 distributions by averaging scores across all
    documents in each day.

    Returns one DailyDistribution per day in the corpus that has at least
    one scored document. The distribution is the per-day MEAN of each
    hypothesis score (averaged across documents published that day),
    normalized to sum to 1.0 for entropy and modal-hypothesis purposes.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT
                    DATE(d.published_at AT TIME ZONE 'UTC') AS day,
                    s.hypothesis_id,
                    AVG(s.score)::real AS avg_score,
                    COUNT(DISTINCT d.id)::int AS doc_count
                FROM documents d
                JOIN document_hypothesis_scores s ON s.document_id = d.id
                WHERE d.corpus_version = %s
                  AND s.prompt_version = %s
                  AND s.model = %s
                  AND d.published_at IS NOT NULL
                GROUP BY DATE(d.published_at AT TIME ZONE 'UTC'), s.hypothesis_id
                ORDER BY day, s.hypothesis_id
                """,
            (corpus_version, prompt_version, model),
        )
        rows = cur.fetchall()

    by_day: dict[date, dict[str, float]] = {}
    doc_counts: dict[date, int] = {}
    for row in rows:
        day = row["day"]
        by_day.setdefault(day, {})[row["hypothesis_id"]] = float(row["avg_score"])
        doc_counts[day] = max(doc_counts.get(day, 0), int(row["doc_count"]))

    output: list[DailyDistribution] = []
    for day in sorted(by_day.keys()):
        raw = by_day[day]
        # Make sure all five hypotheses are present (default 0.0)
        for h in ("H1", "H2", "H3", "H4", "H5"):
            raw.setdefault(h, 0.0)
        total = sum(raw.values())
        normalized = (
            {h: v / total for h, v in raw.items()} if total > 0 else dict.fromkeys(raw, 0.0)
        )
        entropy = _shannon_entropy_bits(list(raw.values()))
        modal_h = max(normalized.keys(), key=lambda k: normalized[k])
        output.append(
            DailyDistribution(
                day=day,
                document_count=doc_counts.get(day, 0),
                distribution=normalized,
                entropy=entropy,
                modal_hypothesis=modal_h,
                modal_probability=normalized[modal_h],
            )
        )
    return output


def upsert_daily_distributions(
    *,
    topic: str,
    corpus_version: str,
    prompt_version: str,
    model: str,
    distributions: list[DailyDistribution],
) -> int:
    """Persist a list of DailyDistribution rows to hypothesis_distributions.

    Idempotent on (topic, corpus_version, day, prompt_version, model).
    Different corpus versions for the same topic coexist as separate rows;
    a re-run for the same corpus version updates in place.
    """
    if not distributions:
        return 0

    now = datetime.now(UTC)
    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for d in distributions:
            day_dt = datetime.combine(d.day, datetime.min.time(), tzinfo=UTC)
            key = f"{topic}|{corpus_version}|{day_dt.isoformat()}|{prompt_version}|{model}".encode()
            row_id = "hd_" + hashlib.sha1(key).hexdigest()[:24]
            cur.execute(
                """
                    INSERT INTO hypothesis_distributions (
                        id, topic, corpus_version, day, document_count,
                        distribution, entropy, modal_hypothesis,
                        modal_probability, prompt_version, model, computed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (topic, corpus_version, day, prompt_version, model)
                    DO UPDATE SET
                        document_count = EXCLUDED.document_count,
                        distribution = EXCLUDED.distribution,
                        entropy = EXCLUDED.entropy,
                        modal_hypothesis = EXCLUDED.modal_hypothesis,
                        modal_probability = EXCLUDED.modal_probability,
                        computed_at = EXCLUDED.computed_at
                    """,
                (
                    row_id,
                    topic,
                    corpus_version,
                    day_dt,
                    d.document_count,
                    psycopg.types.json.Jsonb(d.distribution),
                    d.entropy,
                    d.modal_hypothesis,
                    d.modal_probability,
                    prompt_version,
                    model,
                    now,
                ),
            )
            affected += 1
    return affected


def load_daily_distributions(
    *,
    topic: str,
    corpus_version: str,
    prompt_version: str,
    model: str,
) -> list[dict[str, object]]:
    """Load the persisted daily distributions for a topic and corpus, sorted by day."""
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT day, document_count, distribution, entropy,
                       modal_hypothesis, modal_probability
                FROM hypothesis_distributions
                WHERE topic = %s AND corpus_version = %s
                  AND prompt_version = %s AND model = %s
                ORDER BY day ASC
                """,
            (topic, corpus_version, prompt_version, model),
        )
        return cur.fetchall()
