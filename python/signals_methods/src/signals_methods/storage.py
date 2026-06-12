"""Storage helpers for signals_methods.

Thin wrapper around psycopg for reading corpus documents (input to IVI, NVD,
and SIG) and writing signal rows (output). Imported only by the CLI layer;
the method cores have no database dependency so they can be unit-tested
against in-memory fixtures.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

import psycopg
from signals_core import neon_connection


@dataclass(frozen=True)
class CorpusDocument:
    """A document loaded from the corpus for signal computation."""

    published_at: datetime
    source_kind: str


def load_corpus_documents(corpus_version: str) -> list[CorpusDocument]:
    """Load all documents in a corpus with their source kind joined.

    Skips documents with null published_at; those cannot contribute to
    a time series. Returns an empty list if the corpus is empty.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT d.published_at, s.kind AS source_kind
                FROM documents d
                JOIN sources s ON s.id = d.source_id
                WHERE d.corpus_version = %s
                  AND d.published_at IS NOT NULL
                ORDER BY d.published_at ASC
                """,
            (corpus_version,),
        )
        rows = cur.fetchall()
    return [
        CorpusDocument(
            published_at=row["published_at"],
            source_kind=row["source_kind"],
        )
        for row in rows
    ]


def upsert_ivi_rows(
    *,
    topic: str,
    corpus_version: str,
    window_days: int,
    rows: list[dict[str, object]],
) -> int:
    """Insert or update a batch of IVI rows.

    Idempotency is keyed on (topic, window_end, window_days). Calling
    `compute ivi` twice with the same topic and window size overwrites
    rather than duplicating. Returns the number of rows affected.

    Each row in `rows` must contain the IviResult-as-dict shape plus
    the discourse_count, authoritative_count, and window bounds.
    """
    if not rows:
        return 0

    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for r in rows:
            # Stable deterministic id per (topic, window_end, window_days)
            # so ON CONFLICT can update in place. Not a ULID because we
            # want the same row to keep the same id on recompute.
            key = f"{topic}|{r['window_end']}|{window_days}".encode()
            row_id = "ivi_" + hashlib.sha1(key).hexdigest()[:24]

            cur.execute(
                """
                    INSERT INTO signal_ivi (
                        id, topic, corpus_version, window_start, window_end,
                        window_days, discourse_count, authoritative_count,
                        value, components, computed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (topic, window_end, window_days) DO UPDATE
                        SET corpus_version = EXCLUDED.corpus_version,
                            window_start = EXCLUDED.window_start,
                            discourse_count = EXCLUDED.discourse_count,
                            authoritative_count = EXCLUDED.authoritative_count,
                            value = EXCLUDED.value,
                            components = EXCLUDED.components,
                            computed_at = EXCLUDED.computed_at
                    """,
                (
                    row_id,
                    topic,
                    corpus_version,
                    r["window_start"],
                    r["window_end"],
                    window_days,
                    r["discourse_count"],
                    r["authoritative_count"],
                    r["value"],
                    psycopg.types.json.Jsonb(r.get("components") or {}),
                    datetime.now(UTC),
                ),
            )
            affected += 1
    return affected


def load_ivi_series(
    *,
    topic: str,
    window_days: int,
) -> list[dict[str, object]]:
    """Load the IVI time series for a topic from Neon.

    Returns rows sorted by window_end ascending. Note: the signal_ivi
    unique key is (topic, window_end, window_days) without corpus_version,
    so only the latest computed corpus survives per window. Filtering by
    corpus_version here would return empty after recomputation overwrites
    the rows. Callers that need per-corpus reproducibility should version
    at the advisory level, not the IVI level.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT window_start, window_end, discourse_count,
                       authoritative_count, value
                FROM signal_ivi
                WHERE topic = %s AND window_days = %s
                ORDER BY window_end ASC
                """,
            (topic, window_days),
        )
        return cur.fetchall()


# ---------------------------------------------------------------------------
# NVD storage helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NvdCorpusDocument:
    """A document record for NVD/SIG computation (includes title and URL)."""

    document_id: str
    published_at: datetime
    title: str
    url: str


@dataclass(frozen=True)
class RawHypothesisScore:
    """A raw hypothesis score row from document_hypothesis_scores."""

    document_id: str
    hypothesis_id: str
    score: float


def load_corpus_documents_for_nvd(
    corpus_version: str,
    *,
    prompt_version: str,
    model: str,
) -> tuple[list[NvdCorpusDocument], list[RawHypothesisScore]]:
    """Load documents and their hypothesis scores for NVD/SIG computation.

    Returns two parallel lists:
    - documents: all corpus documents with non-null published_at + title
    - scores: all document_hypothesis_scores rows for the given prompt/model

    Documents with no corresponding hypothesis scores still appear in the
    document list; they simply contribute zero evidence velocity.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT d.id, d.published_at, COALESCE(d.title, '') AS title, d.url
                FROM documents d
                WHERE d.corpus_version = %s
                  AND d.published_at IS NOT NULL
                ORDER BY d.published_at ASC
                """,
            (corpus_version,),
        )
        doc_rows = cur.fetchall()

        cur.execute(
            """
                SELECT s.document_id, s.hypothesis_id, s.score
                FROM document_hypothesis_scores s
                JOIN documents d ON d.id = s.document_id
                WHERE d.corpus_version = %s
                  AND s.prompt_version = %s
                  AND s.model = %s
                """,
            (corpus_version, prompt_version, model),
        )
        score_rows = cur.fetchall()

    docs = [
        NvdCorpusDocument(
            document_id=r["id"],
            published_at=r["published_at"],
            title=r["title"],
            url=r["url"],
        )
        for r in doc_rows
    ]
    scores = [
        RawHypothesisScore(
            document_id=r["document_id"],
            hypothesis_id=r["hypothesis_id"],
            score=float(r["score"]),
        )
        for r in score_rows
    ]
    return docs, scores


def upsert_nvd_rows(
    *,
    topic: str,
    corpus_version: str,
    window_days: int,
    rows: list[dict[str, object]],
) -> int:
    """Upsert NVD rows to signal_nvd.

    Idempotent on (topic, corpus_version, narrative_slug, window_end, window_days).
    """
    if not rows:
        return 0

    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for r in rows:
            key = (
                f"{topic}|{corpus_version}|{r['narrative_slug']}|{r['window_end']}|{window_days}"
            ).encode()
            row_id = "nvd_" + hashlib.sha1(key).hexdigest()[:24]
            cur.execute(
                """
                    INSERT INTO signal_nvd (
                        id, topic, corpus_version, narrative_slug,
                        window_start, window_end, window_days,
                        narrative_velocity, evidence_velocity, nvd_value, computed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (topic, corpus_version, narrative_slug, window_end, window_days)
                    DO UPDATE SET
                        window_start = EXCLUDED.window_start,
                        narrative_velocity = EXCLUDED.narrative_velocity,
                        evidence_velocity = EXCLUDED.evidence_velocity,
                        nvd_value = EXCLUDED.nvd_value,
                        computed_at = EXCLUDED.computed_at
                    """,
                (
                    row_id,
                    topic,
                    corpus_version,
                    r["narrative_slug"],
                    r["window_start"],
                    r["window_end"],
                    window_days,
                    r["narrative_velocity"],
                    r["evidence_velocity"],
                    r["nvd_value"],
                    datetime.now(UTC),
                ),
            )
            affected += 1
    return affected


def load_nvd_series(
    *,
    topic: str,
    corpus_version: str,
    window_days: int,
) -> list[dict[str, object]]:
    """Load NVD time series for a topic, ordered by narrative then date."""
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT narrative_slug, window_start, window_end,
                       narrative_velocity, evidence_velocity, nvd_value
                FROM signal_nvd
                WHERE topic = %s AND corpus_version = %s AND window_days = %s
                ORDER BY narrative_slug, window_end ASC
                """,
            (topic, corpus_version, window_days),
        )
        return cur.fetchall()


# ---------------------------------------------------------------------------
# Source Independence Graph storage helpers
# ---------------------------------------------------------------------------


def upsert_independence_rows(
    *,
    topic: str,
    corpus_version: str,
    rows: list[dict[str, object]],
) -> int:
    """Upsert SIG result rows to signal_independence.

    Idempotent on (topic, corpus_version, narrative_slug).
    """
    if not rows:
        return 0

    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for r in rows:
            key = f"{topic}|{corpus_version}|{r['narrative_slug']}".encode()
            row_id = "sig_" + hashlib.sha1(key).hexdigest()[:24]
            cur.execute(
                """
                    INSERT INTO signal_independence (
                        id, topic, corpus_version, narrative_slug,
                        narrative_label, origin_label,
                        total_documents, unique_domains,
                        independent_sources, amplifier_sources,
                        independence_score, amplification_ratio,
                        graph_data, computed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (topic, corpus_version, narrative_slug)
                    DO UPDATE SET
                        narrative_label = EXCLUDED.narrative_label,
                        origin_label = EXCLUDED.origin_label,
                        total_documents = EXCLUDED.total_documents,
                        unique_domains = EXCLUDED.unique_domains,
                        independent_sources = EXCLUDED.independent_sources,
                        amplifier_sources = EXCLUDED.amplifier_sources,
                        independence_score = EXCLUDED.independence_score,
                        amplification_ratio = EXCLUDED.amplification_ratio,
                        graph_data = EXCLUDED.graph_data,
                        computed_at = EXCLUDED.computed_at
                    """,
                (
                    row_id,
                    topic,
                    corpus_version,
                    r["narrative_slug"],
                    r["narrative_label"],
                    r["origin_label"],
                    r["total_documents"],
                    r["unique_domains"],
                    r["independent_sources"],
                    r["amplifier_sources"],
                    r["independence_score"],
                    r["amplification_ratio"],
                    psycopg.types.json.Jsonb(r.get("graph_data") or {}),
                    datetime.now(UTC),
                ),
            )
            affected += 1
    return affected


def load_independence_rows(
    *,
    topic: str,
    corpus_version: str,
) -> list[dict[str, object]]:
    """Load SIG results for a topic, ordered by independence_score ascending."""
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT narrative_slug, narrative_label, origin_label,
                       total_documents, unique_domains,
                       independent_sources, amplifier_sources,
                       independence_score, amplification_ratio
                FROM signal_independence
                WHERE topic = %s AND corpus_version = %s
                ORDER BY independence_score ASC
                """,
            (topic, corpus_version),
        )
        return cur.fetchall()


# ---------------------------------------------------------------------------
# Hypothesis distribution helpers (for SQM eval)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Advisory storage helpers
# ---------------------------------------------------------------------------


def upsert_advisory_rows(
    *,
    topic: str,
    corpus_version: str,
    rows: list[dict[str, object]],
) -> int:
    """Upsert advisory rows to the advisories table.

    Idempotent on (topic, corpus_version, controller_slug, signal_trigger,
    narrative_slug, advisory_date). The corpus_version dimension ensures
    advisories from different corpus snapshots coexist for reproducibility
    and cross-corpus comparison.
    """
    if not rows:
        return 0

    affected = 0
    with neon_connection() as conn, conn.cursor() as cur:
        for r in rows:
            # Coalesce narrative_slug to empty string for
            # narrative-agnostic advisories (IVI vacuum, entropy floor)
            narr = r.get("narrative_slug") or ""
            key = (
                f"{topic}|{corpus_version}|{r['controller_slug']}|"
                f"{r['signal_trigger']}|{narr}|{r['advisory_date']}"
            ).encode()
            row_id = "adv_" + hashlib.sha1(key).hexdigest()[:24]

            cur.execute(
                """
                    INSERT INTO advisories (
                        id, topic, corpus_version, controller_slug,
                        narrative_slug, signal_trigger, signal_values,
                        advisory_type, severity,
                        recommendation, rationale,
                        klein_activity, stamp_failure_mode,
                        status, advisory_date, created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (
                        topic, corpus_version, controller_slug,
                        signal_trigger, narrative_slug, advisory_date
                    )
                    DO UPDATE SET
                        signal_values = EXCLUDED.signal_values,
                        advisory_type = EXCLUDED.advisory_type,
                        severity = EXCLUDED.severity,
                        recommendation = EXCLUDED.recommendation,
                        rationale = EXCLUDED.rationale,
                        klein_activity = EXCLUDED.klein_activity,
                        stamp_failure_mode = EXCLUDED.stamp_failure_mode,
                        created_at = EXCLUDED.created_at
                    """,
                (
                    row_id,
                    topic,
                    corpus_version,
                    r["controller_slug"],
                    narr,  # coalesced to "" for NULL-safe unique index
                    r["signal_trigger"],
                    psycopg.types.json.Jsonb(r.get("signal_values") or {}),
                    r["advisory_type"],
                    r["severity"],
                    r["recommendation"],
                    r["rationale"],
                    r.get("klein_activity"),
                    r["stamp_failure_mode"],
                    r.get("status", "open"),
                    r["advisory_date"],
                    datetime.now(UTC),
                ),
            )
            affected += 1
    return affected


def load_advisories(
    *,
    topic: str,
    corpus_version: str | None = None,
    controller_slug: str | None = None,
    severity: str | None = None,
) -> list[dict[str, object]]:
    """Load advisories from Neon, optionally filtered by corpus, controller, or severity."""
    with neon_connection() as conn, conn.cursor() as cur:
        query = """
                SELECT corpus_version, controller_slug, narrative_slug,
                       signal_trigger, signal_values, advisory_type, severity,
                       recommendation, rationale, klein_activity,
                       stamp_failure_mode, status, advisory_date, created_at
                FROM advisories
                WHERE topic = %s
            """
        params: list[object] = [topic]

        if corpus_version is not None:
            query += " AND corpus_version = %s"
            params.append(corpus_version)

        if controller_slug is not None:
            query += " AND controller_slug = %s"
            params.append(controller_slug)
        if severity is not None:
            query += " AND severity = %s"
            params.append(severity)

        query += " ORDER BY advisory_date ASC, severity ASC"

        cur.execute(query, params)
        return cur.fetchall()


def load_daily_distributions(
    *,
    topic: str,
    corpus_version: str,
    prompt_version: str,
    model: str,
) -> list[dict[str, object]]:
    """Load the persisted daily hypothesis distributions from hypothesis_distributions.

    Returns dicts with keys {day, entropy_bits, ...}, mapped from the schema's
    entropy column. This duplicates the query in signals_analyze.storage but
    keeps signals_methods independent of signals_analyze.
    """
    with neon_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT day, document_count, distribution,
                       entropy AS entropy_bits,
                       modal_hypothesis, modal_probability
                FROM hypothesis_distributions
                WHERE topic = %s AND corpus_version = %s
                  AND prompt_version = %s AND model = %s
                ORDER BY day ASC
                """,
            (topic, corpus_version, prompt_version, model),
        )
        return cur.fetchall()
