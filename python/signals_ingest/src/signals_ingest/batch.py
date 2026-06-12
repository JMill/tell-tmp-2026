"""Batch ingestion orchestrator.

Reads a seed URL YAML file (see data/<topic>/seed-urls.yaml), iterates each
entry, dispatches to the appropriate adapter, and writes a run summary.

Failures are isolated per entry — a single failing URL does not stop the
batch. The summary at the end lists every success and failure with enough
detail to re-run individual entries by hand.

This is the entry point for Phase A (corpus building). It is deliberately
simple: no concurrency, no retries beyond what each adapter does internally,
no checkpointing. Those are additions for later phases if volume warrants.
For the NJ drones retrospective (~40-60 URLs) sequential execution is
enough and makes debugging easier.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from signals_ingest.adapters import direct as direct_adapter
from signals_ingest.adapters import wayback as wayback_adapter
from signals_ingest.adapters.wayback import IngestResult

# Sleep between consecutive requests in a batch to avoid rate limiting on
# archive.org (the Wayback CDX API aggressively throttles bursts) and to
# be a good citizen on any other rate-limited source.
INTER_REQUEST_DELAY_SECONDS = 1.5


@dataclass
class SeedEntry:
    """One row from a seed-urls.yaml file."""

    url: str
    source_kind: str
    adapter: str  # "wayback" | "direct"
    event_date: str | None = None
    narratives: list[str] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SeedEntry:
        return cls(
            url=data["url"],
            source_kind=data.get("source_kind", "news"),
            adapter=data.get("adapter", "wayback"),
            event_date=data.get("event_date"),
            narratives=list(data.get("narratives", [])),
            notes=data.get("notes"),
        )


@dataclass
class BatchSummary:
    """Outcome of a batch run."""

    corpus_version: str
    seeds_path: str
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    successes: list[tuple[str, IngestResult]] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)  # (url, error_message)


def load_seed_file(path: Path) -> list[SeedEntry]:
    """Parse a seed-urls.yaml file and return a list of SeedEntry objects.

    The file is expected to have a top-level `seeds` key with a list of
    dictionaries. Any other top-level keys (e.g. `metadata`) are ignored.
    """
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "seeds" not in data:
        raise ValueError(f"{path}: seed file must have a top-level 'seeds' key")

    raw_seeds = data["seeds"]
    if not isinstance(raw_seeds, list):
        raise ValueError(f"{path}: 'seeds' must be a list")

    return [SeedEntry.from_dict(s) for s in raw_seeds]


def run_batch(
    *,
    seeds: list[SeedEntry],
    corpus_version: str,
    seeds_path: str,
    on_progress: Any = None,
) -> BatchSummary:
    """Ingest each seed entry into the given corpus version.

    Dispatches to the Wayback or direct adapter based on the entry's
    `adapter` field. Isolates failures per entry so the batch continues
    after any single error.

    `on_progress` is an optional callable invoked with
    (index, total, entry, result_or_exception) after each entry finishes.
    The signature accepts the current running summary via the last arg
    so the caller can render a live progress view.
    """
    summary = BatchSummary(
        corpus_version=corpus_version,
        seeds_path=seeds_path,
        total=len(seeds),
    )

    for i, entry in enumerate(seeds, start=1):
        if i > 1:
            time.sleep(INTER_REQUEST_DELAY_SECONDS)
        try:
            if entry.adapter == "wayback":
                result = wayback_adapter.ingest_url(
                    url=entry.url,
                    corpus_version=corpus_version,
                    source_kind=entry.source_kind,
                )
            elif entry.adapter == "direct":
                result = direct_adapter.ingest_url(
                    url=entry.url,
                    corpus_version=corpus_version,
                    source_kind=entry.source_kind,
                )
            else:
                raise ValueError(f"unknown adapter: {entry.adapter!r}")

            summary.succeeded += 1
            summary.successes.append((entry.url, result))
            if on_progress is not None:
                on_progress(i, len(seeds), entry, result)

        except Exception as exc:
            summary.failed += 1
            summary.failures.append((entry.url, f"{type(exc).__name__}: {exc}"))
            if on_progress is not None:
                on_progress(i, len(seeds), entry, exc)

    return summary
