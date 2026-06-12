"""Shared primitives for the TELL weak signal detection pipeline.

Contains the pydantic data models that serve as the cross-language source of
truth, plus shared utilities (env loading, db connections, date parsing,
display formatting, HTML extraction, ingestion adapter base) that are used
across signals_ingest, signals_analyze, and signals_methods.
"""

from signals_core.dates import (
    parse_published_at,
    parse_wayback_timestamp,
    to_utc,
    utcnow,
)
from signals_core.db import get_database_url, neon_connection
from signals_core.display import make_pipeline_progress, make_summary_table
from signals_core.env import load_env
from signals_core.extract import ExtractedContent, extract_from_html
from signals_core.models import (
    CorpusVersion,
    Document,
    DocumentHypothesisScore,
    EvidenceWeight,
    Hypothesis,
    HypothesisId,
    IviSignalRow,
    Narrative,
    NarrativeCategory,
    Source,
    SourceKind,
)

__all__ = [
    "CorpusVersion",
    "Document",
    "DocumentHypothesisScore",
    "EvidenceWeight",
    "ExtractedContent",
    "Hypothesis",
    "HypothesisId",
    "IviSignalRow",
    "Narrative",
    "NarrativeCategory",
    "Source",
    "SourceKind",
    "extract_from_html",
    "get_database_url",
    "load_env",
    "make_pipeline_progress",
    "make_summary_table",
    "neon_connection",
    "parse_published_at",
    "parse_wayback_timestamp",
    "to_utc",
    "utcnow",
]
