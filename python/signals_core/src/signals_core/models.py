"""Source-of-truth pydantic v2 data models for the OSINT pipeline.

These models are the canonical schema. The TypeScript side mirrors these in
Zod; a CI job regenerates the Zod definitions from JSON Schema emitted by
these pydantic models.

Conventions:
- IDs are ULIDs (string-encoded, sortable, url-safe).
- Timestamps are timezone-aware datetimes (UTC).
- All field names are snake_case.
- Optional fields explicitly use `| None` and default to None where appropriate.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from ulid import ULID


def _new_id() -> str:
    """Generate a new ULID as a string. Sortable by creation time."""
    return str(ULID())


class SourceKind(StrEnum):
    """High-level classification of where a document originates.

    These categories drive the Source Reliability Graph and feed into the
    Bayesian prior selection for H1-H5 hypothesis evaluation.
    """

    GOV = "gov"
    NEWS = "news"
    SOCIAL = "social"
    ACADEMIC = "academic"
    AVIATION = "aviation"
    FORUM = "forum"
    PODCAST = "podcast"
    OTHER = "other"


class EvidenceWeight(StrEnum):
    """Qualitative evidence weight for a claim or document.

    Used in the ground-truth timeline, in narrative definitions, and in
    source reliability scoring.
    """

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    RUMOR = "rumor"


HypothesisId = Literal["H1", "H2", "H3", "H4", "H5"]
"""The five canonical hypotheses from the CU26 framework.

H1 Data/Sensor Artifact
H2 Natural Physical Source
H3 Human-Made Physical Source (unclassified)
H4 Human-Made Physical Source (classified)
H5 Other (Unknown) Physical Phenomenon
"""


class NarrativeCategory(StrEnum):
    """Narrative categories used to tag competing explanations during an event."""

    ADVERSARY = "adversary"
    DOMESTIC_CLASSIFIED = "domestic-classified"
    DOMESTIC_LEGITIMATE = "domestic-legitimate"
    DISMISSAL = "dismissal"
    CONSPIRACY = "conspiracy"
    UNKNOWN = "unknown"
    OBSERVATION = "observation"


class Source(BaseModel):
    """A source of documents. One Source may produce many Documents."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id, description="ULID")
    domain: str = Field(description="Primary domain, e.g. 'nytimes.com'")
    name: str = Field(description="Human-readable source name")
    kind: SourceKind
    reliability_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Source-level reliability score in [0, 1]. None if unscored.",
    )
    reliability_factors: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Structured SAT framework factors (provenance, track record, independence, specificity)"
        ),
    )
    first_seen_at: datetime = Field(description="When this source first appeared in the corpus")


class Document(BaseModel):
    """A single fetched document from a source.

    Raw content lives in Vercel Blob (keyed by content_blob_key).
    Extracted text may also live in Blob (keyed by extracted_text_blob_key).
    Metadata and structured fields live in Postgres.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id, description="ULID")
    source_id: str = Field(description="Reference to Source.id")
    url: HttpUrl = Field(description="The URL as fetched")
    canonical_url: HttpUrl | None = Field(
        default=None,
        description=(
            "Canonical URL if known "
            "(e.g., after following redirects or unwrapping archive.org URLs)"
        ),
    )
    fetched_at: datetime = Field(description="When this specific fetch occurred")
    published_at: datetime | None = Field(
        default=None,
        description="Publication timestamp if available from the source",
    )
    title: str | None = Field(default=None)
    content_blob_key: str | None = Field(
        default=None,
        description="Blob key for the raw fetched payload, e.g. 'corpus/{version}/{sha256}.html'",
    )
    extracted_text_blob_key: str | None = Field(
        default=None,
        description="Blob key for the extracted plain text, if stored separately",
    )
    content_hash: str = Field(description="SHA-256 of the raw fetched content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific metadata (headers, adapter-specific fields)",
    )
    corpus_version: str = Field(
        description=(
            "Label of the corpus version this document belongs to, e.g. 'nj-drones-2026-04-07'"
        )
    )


class Hypothesis(BaseModel):
    """A canonical hypothesis from the CU26 H1-H5 framework."""

    model_config = ConfigDict(extra="forbid")

    id: HypothesisId
    tagline: str = Field(description="Short label, e.g. 'Artifact'")
    description: str
    prior_civilian: float = Field(ge=0.0, le=1.0)
    prior_military: float = Field(ge=0.0, le=1.0)
    sub_hypotheses: list[str] = Field(default_factory=list)


class DocumentHypothesisScore(BaseModel):
    """A single score of a document against a hypothesis.

    Multiple scores may exist per (document, hypothesis) pair if re-scored
    with different models or prompts. The most recent score for each pair
    is what feeds into the hypothesis distribution for the topic.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    document_id: str
    hypothesis_id: HypothesisId
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability this document supports this hypothesis, in [0, 1]",
    )
    rationale: str | None = Field(
        default=None,
        description="Short LLM-generated explanation of the score",
    )
    model: str = Field(description="Model and version used for scoring, e.g. 'claude-opus-4-6'")
    scored_at: datetime


class Narrative(BaseModel):
    """A competing explanation that circulated during an event.

    Narratives are the target of Narrative Velocity Divergence (NVD) analysis.
    Each narrative is tied to zero or more hypotheses and has an originating
    source when traceable.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    slug: str = Field(description="Stable identifier, e.g. 'iranian-mothership'")
    label: str = Field(description="Human-readable label")
    category: NarrativeCategory
    hypothesis: str | None = Field(
        default=None,
        description="Primary hypothesis this narrative maps to, e.g. 'H4'",
    )
    first_seen: datetime | None = None
    originating_source: str | None = Field(
        default=None,
        description="Free-text description of where this narrative originated",
    )
    claim: str = Field(description="The core claim of the narrative")
    evidence_weight: EvidenceWeight


class IviSignalRow(BaseModel):
    """One row of the Information Vacuum Index time series.

    Mirrors the Drizzle `signal_ivi` table in
    packages/db/src/schema/signal_ivi.ts. The unique constraint on
    (topic, window_end, window_days) makes recomputes idempotent: the
    CLI uses ON CONFLICT DO UPDATE to overwrite prior rows for the same
    topic/window rather than duplicating.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    topic: str
    corpus_version: str
    window_start: datetime
    window_end: datetime
    window_days: int = Field(ge=1)
    discourse_count: int = Field(ge=0)
    authoritative_count: int = Field(ge=0)
    value: float = Field(ge=0.0)
    components: dict[str, Any] | None = None
    computed_at: datetime


class CorpusVersion(BaseModel):
    """A frozen snapshot of a corpus for reproducibility.

    Each run of the ingestion pipeline produces a new corpus version.
    Demos are pinned to a specific version. Evaluation runs reference a
    version so results are reproducible.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    label: str = Field(description="Stable label, e.g. 'nj-drones-2026-04-07'")
    created_at: datetime
    manifest_blob_key: str | None = Field(
        default=None,
        description="Blob key for the manifest YAML",
    )
    document_count: int = Field(ge=0)
    commit_sha: str | None = Field(
        default=None,
        description="Git commit SHA at the time of the corpus build",
    )


# ---------------------------------------------------------------------------
# STAMP controller and advisory models (prescriptive layer)
# ---------------------------------------------------------------------------


class ControllerRole(StrEnum):
    """Role classification for a STAMP controller."""

    INSTITUTIONAL = "institutional"
    POLITICAL = "political"
    MEDIA = "media"
    ANALYST = "analyst"


class StampFunction(StrEnum):
    """STAMP function in the information-environment control structure."""

    CONTROLLER = "controller"
    ACTUATOR = "actuator"
    SENSOR = "sensor"


class AdvisoryType(StrEnum):
    """Classification of what a prescriptive advisory recommends."""

    ACT = "act"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    DISCLOSE = "disclose"


class AdvisorySeverity(StrEnum):
    """Urgency level for a prescriptive advisory."""

    WATCH = "watch"
    ADVISORY = "advisory"
    ALERT = "alert"


class AdvisoryStatus(StrEnum):
    """Lifecycle state of a prescriptive advisory."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ACTED = "acted"
    DISMISSED = "dismissed"
    SUPERSEDED = "superseded"


class ControllerAction(BaseModel):
    """An available control action for a STAMP controller."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(description="Machine-readable action type, e.g. 'issue_statement'")
    label: str = Field(description="Human-readable description of the action")


class ControllerNarrative(BaseModel):
    """A controller's relationship to a specific narrative."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(description="Narrative slug from narratives.yaml")
    relationship: Literal["originator", "responder", "monitor", "amplifier"]


class Controller(BaseModel):
    """A STAMP controller in the information-environment control structure.

    Controllers are institutional or political actors who can issue control
    actions (public statements, investigations, policy changes) in response
    to information-environment conditions. The prescriptive layer maps signal
    conditions to recommended control actions per controller.

    Mirrors the Drizzle `controllers` table and is loaded from
    data/{topic}/controllers.yaml.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    topic: str = Field(description="Topic this controller belongs to, e.g. 'nj-drones'")
    slug: str = Field(description="Stable identifier, e.g. 'faa', 'dhs'")
    label: str = Field(description="Human-readable name")
    role: ControllerRole
    stamp_function: StampFunction
    jurisdiction: str = Field(description="What this controller has authority over")
    available_actions: list[ControllerAction] = Field(default_factory=list)
    information_needs: list[str] = Field(
        default_factory=list,
        description="Signal types relevant to this controller: ivi, nvd, sig",
    )
    narratives: list[ControllerNarrative] = Field(
        default_factory=list,
        description="Narratives this controller is connected to and how",
    )


class Advisory(BaseModel):
    """A prescriptive advisory generated from signal state for a specific controller.

    Advisories are the output of the prescriptive logic layer. Each advisory
    recommends a specific control action to a specific controller based on
    current signal conditions, grounded in STAMP hazard analysis and Klein's
    sensemaking framework.

    Template-based generation ensures auditability and reproducibility.
    Signal values and STAMP failure mode classifications are preserved so
    recommendations are traceable to specific conditions.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    topic: str
    corpus_version: str = Field(description="Corpus version this advisory was generated from")
    controller_slug: str = Field(description="Which controller should act")
    narrative_slug: str = Field(
        default="",
        description=(
            "Which narrative triggered this advisory, "
            "or empty string for narrative-agnostic advisories"
        ),
    )
    signal_trigger: str = Field(
        description="Which signal condition(s) fired, e.g. 'ivi_vacuum', 'capture_risk'",
    )
    signal_values: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Signal values at the time of advisory: {ivi: 17.0, nvd: 1.2, sig_independence: 1}"
        ),
    )
    advisory_type: AdvisoryType
    severity: AdvisorySeverity
    recommendation: str = Field(description="Natural language recommendation text")
    rationale: str = Field(description="Why this recommendation, grounded in signal data")
    klein_activity: str | None = Field(
        default=None,
        description="Which Klein sensemaking activity this advisory supports",
    )
    stamp_failure_mode: str = Field(
        description="Which STAMP failure mode this advisory addresses",
    )
    status: AdvisoryStatus = Field(default=AdvisoryStatus.OPEN)
    advisory_date: datetime = Field(
        description="The date/time this advisory applies to (from the signal window)",
    )
    created_at: datetime = Field(
        description="When this advisory was generated",
    )
    resolved_at: datetime | None = Field(default=None)
