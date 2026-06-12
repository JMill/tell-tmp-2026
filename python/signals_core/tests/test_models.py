"""Unit tests for signals_core pydantic models.

These are the first tests in the repo. They exist to (a) verify the models
import and construct cleanly, (b) catch schema drift when the pydantic
definitions change, and (c) provide a pattern for future tests to follow.

Run with: uv run pytest python/signals_core/tests/
"""

from datetime import UTC, datetime

import pytest
from signals_core.models import (
    CorpusVersion,
    Document,
    DocumentHypothesisScore,
    EvidenceWeight,
    Hypothesis,
    Narrative,
    NarrativeCategory,
    Source,
    SourceKind,
)


def _now() -> datetime:
    return datetime.now(UTC)


def test_source_kind_enum_values() -> None:
    """Source kinds cover the full taxonomy the pipeline reasons about."""
    expected = {"gov", "news", "social", "academic", "aviation", "forum", "podcast", "other"}
    assert {k.value for k in SourceKind} == expected


def test_source_construction() -> None:
    """A Source can be constructed with the minimum required fields."""
    source = Source(
        domain="example.com",
        name="Example",
        kind=SourceKind.NEWS,
        first_seen_at=_now(),
    )
    assert source.domain == "example.com"
    assert source.kind == SourceKind.NEWS
    assert source.reliability_score is None  # optional, unscored by default
    assert source.id  # ULID auto-generated


def test_source_reliability_score_bounds() -> None:
    """Reliability score must be in [0, 1]."""
    with pytest.raises(ValueError):
        Source(
            domain="example.com",
            name="Example",
            kind=SourceKind.NEWS,
            first_seen_at=_now(),
            reliability_score=1.5,
        )
    with pytest.raises(ValueError):
        Source(
            domain="example.com",
            name="Example",
            kind=SourceKind.NEWS,
            first_seen_at=_now(),
            reliability_score=-0.1,
        )


def test_document_construction() -> None:
    """A Document can be constructed with the required fields."""
    doc = Document(
        source_id="01KNPKG1M066H8AXMC6YX9BWRS",
        url="https://example.com/article",
        fetched_at=_now(),
        content_hash="a" * 64,
        corpus_version="test-corpus-2026-04-08",
    )
    # pydantic HttpUrl stringifies with a trailing slash on the host. Compare
    # as a string prefix to tolerate that without being strict about trailing
    # slash behavior across pydantic versions.
    assert str(doc.url).startswith("https://example.com/article")
    assert doc.metadata == {}  # default empty dict
    assert doc.published_at is None


def test_document_rejects_extra_fields() -> None:
    """Models use extra='forbid' to catch schema drift. Adding an unexpected
    field at construction should raise."""
    with pytest.raises(ValueError):
        Document(
            source_id="01KNPKG1M066H8AXMC6YX9BWRS",
            url="https://example.com/article",
            fetched_at=_now(),
            content_hash="a" * 64,
            corpus_version="test-corpus-2026-04-08",
            not_a_real_field="nope",  # type: ignore[call-arg]
        )


def test_hypothesis_priors_valid() -> None:
    """Hypothesis priors must be in [0, 1]."""
    h = Hypothesis(
        id="H1",
        tagline="Artifact",
        description="Data or sensor artifact.",
        prior_civilian=0.2,
        prior_military=0.1,
    )
    assert h.id == "H1"
    assert 0.0 <= h.prior_civilian <= 1.0


def test_document_hypothesis_score_bounds() -> None:
    """Hypothesis scores must be in [0, 1]."""
    score = DocumentHypothesisScore(
        document_id="01KNPKG223P73HQWGYJ3DDRDXW",
        hypothesis_id="H5",
        score=0.42,
        model="claude-opus-4-6",
        scored_at=_now(),
    )
    assert score.hypothesis_id == "H5"
    assert score.score == 0.42

    with pytest.raises(ValueError):
        DocumentHypothesisScore(
            document_id="01KNPKG223P73HQWGYJ3DDRDXW",
            hypothesis_id="H5",
            score=1.5,
            model="claude-opus-4-6",
            scored_at=_now(),
        )


def test_narrative_construction() -> None:
    """A Narrative is the target of NVD analysis and can be constructed from
    the fields in data/nj-drones/narratives.yaml."""
    n = Narrative(
        slug="iranian-mothership",
        label="Iranian Mothership",
        category=NarrativeCategory.ADVERSARY,
        hypothesis="H4",
        claim="An Iranian ship off the East Coast was launching drones.",
        evidence_weight=EvidenceWeight.RUMOR,
    )
    assert n.slug == "iranian-mothership"
    assert n.evidence_weight == EvidenceWeight.RUMOR


def test_corpus_version_nonnegative_count() -> None:
    """Corpus document count cannot be negative."""
    cv = CorpusVersion(
        label="test-corpus-2026-04-08",
        created_at=_now(),
        document_count=0,
    )
    assert cv.document_count == 0

    with pytest.raises(ValueError):
        CorpusVersion(
            label="test-corpus-2026-04-08",
            created_at=_now(),
            document_count=-1,
        )


def test_ulid_ids_sortable() -> None:
    """ULIDs should sort by creation time, which is a load-bearing property
    for timeline-ordered queries that rely on ID order as a tie-breaker."""
    ids = [
        Document(
            source_id="01KNPKG1M066H8AXMC6YX9BWRS",
            url=f"https://example.com/article/{i}",
            fetched_at=_now(),
            content_hash=str(i).ljust(64, "0"),
            corpus_version="test",
        ).id
        for i in range(5)
    ]
    assert ids == sorted(ids), "ULIDs should be monotonically sortable when created in sequence"
