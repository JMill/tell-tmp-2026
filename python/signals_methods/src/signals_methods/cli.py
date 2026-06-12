"""Typer CLI for signals_methods subcommands.

Exposed via the top-level `signals compute ...` CLI aggregator in signals_cli.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from signals_core import load_env

from signals_methods.constants import (
    AUTHORITATIVE_SOURCE_KINDS,
    DISCOURSE_SOURCE_KINDS,
    EVAL_IVI_WINDOW_DAYS,
    IVI_DEFAULT_WINDOW_DAYS,
    NARRATIVE_DEFS,
    NVD_DEFAULT_WINDOW_DAYS,
    load_narrative_defs,
)
from signals_methods.eval import (
    IndependenceResult as EvalIndependenceResult,
)
from signals_methods.eval import (
    IviPoint,
    compute_alignment,
    compute_capture_risk,
    compute_closure_resistance,
    compute_contradicting_evidence_lag,
    load_timeline_from_yaml,
)
from signals_methods.independence import IndependenceResult, compute_independence
from signals_methods.ivi import (
    DEFAULT_WINDOW_DAYS,
    DocumentRecord,
    compute_ivi,
)
from signals_methods.nvd import HypothesisScore, NvdDocument, NvdPoint, compute_nvd
from signals_methods.prescribe import (
    EntropySnapshot,
    NvdSnapshot,
    SigSnapshot,
    generate_advisories,
    load_controllers_yaml,
)
from signals_methods.storage import (
    load_advisories,
    load_corpus_documents,
    load_corpus_documents_for_nvd,
    load_daily_distributions,
    load_independence_rows,
    load_ivi_series,
    load_nvd_series,
    upsert_advisory_rows,
    upsert_independence_rows,
    upsert_ivi_rows,
    upsert_nvd_rows,
)

console = Console()
app = typer.Typer(
    name="compute",
    help="Compute novel weak signal methods over ingested corpora.",
    no_args_is_help=True,
    add_completion=False,
)


def _resolve_narrative_defs(
    narratives_path: Path | None,
) -> list[dict[str, object]]:
    """Return narrative defs for a compute command.

    If --narratives is supplied, load from that path and fail loudly if it
    is missing or empty. Otherwise fall back to the module-level default
    (nj-drones walk-up, loaded at import time). Failing loud on an explicit
    --narratives path is deliberate: silently falling back to the default
    would score the wrong corpus and produce metrics that look reasonable
    but are wrong.
    """
    if narratives_path is None:
        if not NARRATIVE_DEFS:
            console.print(
                "[red]Default narratives.yaml not resolvable from module.[/red] "
                "Pass --narratives explicitly."
            )
            raise typer.Exit(code=1)
        return NARRATIVE_DEFS

    try:
        defs = load_narrative_defs(narratives_path)
    except FileNotFoundError as exc:
        console.print(f"[red]Narratives file not found:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except OSError as exc:
        # IsADirectoryError (user passed --narratives data/nj-drones/ without
        # the trailing /narratives.yaml) and PermissionError (mode bits wrong)
        # are the realistic cases here. Both are OSError subclasses and must
        # be caught after FileNotFoundError, which is itself an OSError.
        console.print(f"[red]Narratives file is not readable:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]Narratives file is malformed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if not defs:
        console.print(f"[red]Narratives file is empty:[/red] {narratives_path}")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Loaded {len(defs)} narrative definitions[/cyan] from {narratives_path}")
    return defs


@app.command()
def ivi(
    corpus_version: str = typer.Option(
        ...,
        "--corpus",
        help="Corpus version label to compute IVI against",
    ),
    topic: str = typer.Option(
        ...,
        "--topic",
        help="Topic identifier (e.g. 'nj-drones'). Free-text, persisted to signal_ivi.",
    ),
    window_days: int = typer.Option(
        DEFAULT_WINDOW_DAYS,
        "--window-days",
        help="Rolling window width in days. Default 7.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Compute but do not persist to Neon. Useful for inspection.",
    ),
) -> None:
    """Compute the Information Vacuum Index time series for a corpus.

    Loads all documents with a non-null published_at from the named
    corpus, partitions them into discourse and authoritative by source
    kind, and computes a rolling-window IVI series covering the corpus
    date range. Persists the series to the `signal_ivi` table.

    Example:
        signals compute ivi --corpus nj-drones-2026-04-08 --topic nj-drones
    """
    load_env()

    console.print(
        f"[cyan]Loading corpus[/cyan] {corpus_version} (topic={topic}, window={window_days}d)"
    )
    try:
        docs = load_corpus_documents(corpus_version)
    except Exception as exc:
        console.print(f"[red]Failed to load corpus:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if not docs:
        console.print(f"[red]No documents with published_at in corpus[/red] {corpus_version}")
        raise typer.Exit(code=1)

    discourse = sum(1 for d in docs if d.source_kind in DISCOURSE_SOURCE_KINDS)
    authoritative = sum(1 for d in docs if d.source_kind in AUTHORITATIVE_SOURCE_KINDS)
    unknown = len(docs) - discourse - authoritative

    header = Table(title="Corpus partition", show_header=False)
    header.add_column("Field", style="cyan")
    header.add_column("Value")
    header.add_row("Total documents", str(len(docs)))
    header.add_row("Discourse (news/social/forum/podcast)", str(discourse))
    header.add_row("Authoritative (gov/academic/aviation)", str(authoritative))
    if unknown:
        header.add_row("Unknown source kind (ignored)", f"[yellow]{unknown}[/yellow]")
    console.print(header)

    records = [DocumentRecord(published_at=d.published_at, source_kind=d.source_kind) for d in docs]
    results = compute_ivi(records, window_days=window_days)
    console.print(f"[green]Computed {len(results)} IVI windows[/green]")

    if results:
        peak = max(results, key=lambda r: r.value)
        console.print(
            f"[cyan]Peak window:[/cyan] "
            f"{peak.window_start.date()} to {peak.window_end.date()}  "
            f"discourse={peak.discourse_count}  "
            f"authoritative={peak.authoritative_count}  "
            f"[bold]IVI={peak.value:.2f}[/bold]"
        )
        top = sorted(results, key=lambda r: r.value, reverse=True)[:10]
        detail = Table(title="Top 10 IVI windows")
        detail.add_column("Window end", style="cyan")
        detail.add_column("Discourse", justify="right")
        detail.add_column("Authoritative", justify="right")
        detail.add_column("IVI", justify="right", style="bold")
        for r in top:
            detail.add_row(
                r.window_end.date().isoformat(),
                str(r.discourse_count),
                str(r.authoritative_count),
                f"{r.value:.2f}",
            )
        console.print(detail)

    if dry_run:
        console.print("[yellow]Dry run; not persisting to Neon.[/yellow]")
        return

    rows_to_persist: list[dict[str, object]] = []
    for r in results:
        rows_to_persist.append(
            {
                "window_start": r.window_start,
                "window_end": r.window_end,
                "discourse_count": r.discourse_count,
                "authoritative_count": r.authoritative_count,
                "value": r.value,
            }
        )

    affected = upsert_ivi_rows(
        topic=topic,
        corpus_version=corpus_version,
        window_days=window_days,
        rows=rows_to_persist,
    )
    console.print(f"[green]Upserted {affected} rows to signal_ivi[/green]")


@app.command("ivi-status")
def ivi_status(
    topic: str = typer.Option(..., "--topic", help="Topic identifier"),
    window_days: int = typer.Option(
        DEFAULT_WINDOW_DAYS,
        "--window-days",
        help="Window width to query",
    ),
    limit: int = typer.Option(15, "--limit", help="Max rows to show"),
) -> None:
    """Show the persisted IVI time series for a topic."""
    load_env()

    rows = load_ivi_series(topic=topic, window_days=window_days)
    if not rows:
        console.print(f"[yellow]No IVI rows for topic[/yellow] {topic}")
        return

    top = sorted(rows, key=lambda r: r["value"], reverse=True)[:limit]
    table = Table(title=f"Top {len(top)} IVI windows for {topic}")
    table.add_column("Window end", style="cyan")
    table.add_column("Discourse", justify="right")
    table.add_column("Authoritative", justify="right")
    table.add_column("IVI", justify="right", style="bold")
    for r in top:
        table.add_row(
            r["window_end"].date().isoformat(),
            str(r["discourse_count"]),
            str(r["authoritative_count"]),
            f"{r['value']:.2f}",
        )
    console.print(table)
    console.print(f"Total persisted rows: {len(rows)}")


@app.command()
def nvd(
    corpus_version: str = typer.Option(..., "--corpus", help="Corpus version label"),
    topic: str = typer.Option(..., "--topic", help="Topic identifier"),
    prompt_version: str = typer.Option("h15-v1", "--prompt-version"),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model"),
    window_days: int = typer.Option(
        NVD_DEFAULT_WINDOW_DAYS,
        "--window-days",
        help="Rolling window width in days (default 3).",
    ),
    narratives_path: Path = typer.Option(
        None,
        "--narratives",
        help=(
            "Path to narratives.yaml. Defaults to the nj-drones walk-up loaded at "
            "import time. Pass an explicit path to score a different corpus against "
            "its own narrative definitions."
        ),
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Compute Narrative Velocity Divergence over the corpus.

    Classifies documents into pre-defined narratives via keyword matching,
    then for each narrative computes a rolling-window ratio of narrative
    spread vs. hypothesis-supported evidence. Requires Phase C hypothesis
    scores to already be populated.

    Example:
        signals compute nvd --corpus nj-drones-2026-04-08 --topic nj-drones
    """
    load_env()
    console.print(f"[cyan]Loading corpus[/cyan] {corpus_version} for NVD")

    raw_docs, raw_scores = load_corpus_documents_for_nvd(
        corpus_version,
        prompt_version=prompt_version,
        model=model,
    )
    if not raw_docs:
        console.print(f"[red]No documents in corpus[/red] {corpus_version}")
        raise typer.Exit(code=1)

    if not raw_scores:
        console.print(
            "[red]No hypothesis scores found[/red] for corpus "
            f"{corpus_version} (prompt={prompt_version}, model={model}). "
            "Run Phase C hypothesis scoring first."
        )
        raise typer.Exit(code=1)

    scored_doc_ids = {s.document_id for s in raw_scores}
    unscored = [d for d in raw_docs if d.document_id not in scored_doc_ids]
    if unscored:
        console.print(
            f"[red]Partial coverage[/red]: {len(unscored)} of {len(raw_docs)} documents "
            f"have no hypothesis scores (prompt={prompt_version}, model={model}). "
            "NVD values would be artificially inflated. "
            "Re-run Phase C or filter the corpus to fully-scored documents."
        )
        raise typer.Exit(code=1)

    console.print(f"  {len(raw_docs)} documents, {len(raw_scores)} hypothesis scores")

    nvd_docs = [
        NvdDocument(
            document_id=d.document_id,
            published_at=d.published_at,
            title=d.title,
            url=d.url,
        )
        for d in raw_docs
    ]
    h_scores = [
        HypothesisScore(
            document_id=s.document_id,
            hypothesis_id=s.hypothesis_id,
            score=s.score,
        )
        for s in raw_scores
    ]

    narrative_defs = _resolve_narrative_defs(narratives_path)
    points = compute_nvd(
        nvd_docs,
        h_scores,
        window_days=window_days,
        narrative_defs=narrative_defs,
    )
    console.print(f"[green]Computed {len(points)} NVD points[/green] ({window_days}d window)")

    # Show the top NVD readings per narrative
    from collections import defaultdict

    by_narrative: dict[str, list] = defaultdict(list)
    for p in points:
        by_narrative[p.narrative_slug].append(p)

    detail = Table(title="Peak NVD per narrative")
    detail.add_column("Narrative", style="cyan")
    detail.add_column("Peak date", justify="right")
    detail.add_column("N.vel", justify="right")
    detail.add_column("E.vel", justify="right")
    detail.add_column("NVD", justify="right", style="bold")
    for slug, pts in sorted(by_narrative.items()):
        peak = max(pts, key=lambda p: p.nvd_value)
        detail.add_row(
            slug,
            peak.window_end.date().isoformat(),
            str(peak.narrative_velocity),
            str(peak.evidence_velocity),
            f"{peak.nvd_value:.2f}",
        )
    console.print(detail)

    if dry_run:
        console.print("[yellow]Dry run; not persisting.[/yellow]")
        return

    rows_to_upsert = [
        {
            "narrative_slug": p.narrative_slug,
            "window_start": p.window_start,
            "window_end": p.window_end,
            "narrative_velocity": p.narrative_velocity,
            "evidence_velocity": p.evidence_velocity,
            "nvd_value": p.nvd_value,
        }
        for p in points
    ]
    affected = upsert_nvd_rows(
        topic=topic,
        corpus_version=corpus_version,
        window_days=window_days,
        rows=rows_to_upsert,
    )
    console.print(f"[green]Upserted {affected} rows to signal_nvd[/green]")


@app.command("nvd-status")
def nvd_status(
    topic: str = typer.Option(..., "--topic"),
    corpus_version: str = typer.Option(..., "--corpus"),
    window_days: int = typer.Option(NVD_DEFAULT_WINDOW_DAYS, "--window-days"),
    narrative: str | None = typer.Option(None, "--narrative", help="Filter to one narrative slug"),
) -> None:
    """Show the persisted NVD time series for a topic and corpus."""
    load_env()
    rows = load_nvd_series(topic=topic, corpus_version=corpus_version, window_days=window_days)
    if not rows:
        console.print(f"[yellow]No NVD rows for topic {topic} corpus {corpus_version}[/yellow]")
        return

    if narrative:
        rows = [r for r in rows if r["narrative_slug"] == narrative]

    table = Table(title=f"NVD series for {topic} ({corpus_version})")
    table.add_column("Narrative", style="cyan")
    table.add_column("Window end", justify="right")
    table.add_column("N.vel", justify="right")
    table.add_column("E.vel", justify="right")
    table.add_column("NVD", justify="right", style="bold")
    for r in rows:
        table.add_row(
            str(r["narrative_slug"]),
            r["window_end"].date().isoformat(),
            str(r["narrative_velocity"]),
            str(r["evidence_velocity"]),
            f"{r['nvd_value']:.2f}",
        )
    console.print(table)
    console.print(f"Total rows: {len(rows)}")


@app.command()
def independence(
    corpus_version: str = typer.Option(..., "--corpus"),
    topic: str = typer.Option(..., "--topic"),
    prompt_version: str = typer.Option("h15-v1", "--prompt-version"),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model"),
    narratives_path: Path = typer.Option(
        None,
        "--narratives",
        help=(
            "Path to narratives.yaml. Defaults to the nj-drones walk-up loaded at "
            "import time. Pass an explicit path to score a different corpus against "
            "its own narrative definitions."
        ),
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Compute the Source Independence Graph for each narrative.

    Maps corpus documents to narratives via keyword matching, then classifies
    each source domain as independent (making an original claim) or amplifier
    (repeating another source's claim). The independence score is the count of
    independent sources + 1 (the originating source).

    Example:
        signals compute independence --corpus nj-drones-2026-04-08 --topic nj-drones
    """
    load_env()
    console.print(f"[cyan]Loading corpus[/cyan] {corpus_version} for SIG")

    raw_docs, _ = load_corpus_documents_for_nvd(
        corpus_version,
        prompt_version=prompt_version,
        model=model,
    )
    if not raw_docs:
        console.print(f"[red]No documents in corpus[/red] {corpus_version}")
        raise typer.Exit(code=1)

    console.print(f"  {len(raw_docs)} documents")

    nvd_docs = [
        NvdDocument(
            document_id=d.document_id,
            published_at=d.published_at,
            title=d.title,
            url=d.url,
        )
        for d in raw_docs
    ]

    narrative_defs = _resolve_narrative_defs(narratives_path)
    results: list[IndependenceResult] = compute_independence(
        nvd_docs,
        narrative_defs=narrative_defs,
    )

    table = Table(title=f"Source Independence Graph: {topic} ({corpus_version})")
    table.add_column("Narrative", style="cyan")
    table.add_column("Docs", justify="right")
    table.add_column("Domains", justify="right")
    table.add_column("Independent", justify="right")
    table.add_column("Amplifiers", justify="right")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Amplification ×", justify="right")
    for r in results:
        table.add_row(
            r.narrative_slug,
            str(r.total_documents),
            str(r.unique_domains),
            str(r.independent_sources),
            str(r.amplifier_sources),
            f"{r.independence_score:.0f}",
            f"{r.amplification_ratio:.1f}×",
        )
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run; not persisting.[/yellow]")
        return

    rows_to_upsert = [
        {
            "narrative_slug": r.narrative_slug,
            "narrative_label": r.narrative_label,
            "origin_label": r.origin_label,
            "total_documents": r.total_documents,
            "unique_domains": r.unique_domains,
            "independent_sources": r.independent_sources,
            "amplifier_sources": r.amplifier_sources,
            "independence_score": r.independence_score,
            "amplification_ratio": r.amplification_ratio,
            "graph_data": {
                "sources": [
                    {
                        "domain": s.domain,
                        "role": s.role,
                        "document_count": s.document_count,
                    }
                    for s in r.sources
                ]
            },
        }
        for r in results
    ]
    affected = upsert_independence_rows(
        topic=topic,
        corpus_version=corpus_version,
        rows=rows_to_upsert,
    )
    console.print(f"[green]Upserted {affected} rows to signal_independence[/green]")


@app.command("independence-status")
def independence_status(
    topic: str = typer.Option(..., "--topic"),
    corpus_version: str = typer.Option(..., "--corpus"),
) -> None:
    """Show the persisted Source Independence Graph results for a topic."""
    load_env()
    rows = load_independence_rows(topic=topic, corpus_version=corpus_version)
    if not rows:
        console.print(f"[yellow]No SIG rows for {topic} {corpus_version}[/yellow]")
        return

    table = Table(title=f"Source Independence Graph: {topic} ({corpus_version})")
    table.add_column("Narrative", style="cyan")
    table.add_column("Docs", justify="right")
    table.add_column("Domains", justify="right")
    table.add_column("Independent", justify="right")
    table.add_column("Amplifiers", justify="right")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Amplification ×", justify="right")
    for r in rows:
        table.add_row(
            str(r["narrative_slug"]),
            str(r["total_documents"]),
            str(r["unique_domains"]),
            str(r["independent_sources"]),
            str(r["amplifier_sources"]),
            f"{r['independence_score']:.0f}",
            f"{r['amplification_ratio']:.1f}×",
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Sensemaking Quality Metrics (SQM) evaluation
# ---------------------------------------------------------------------------


@app.command("eval")
def sqm_eval(
    corpus_version: str = typer.Option(..., "--corpus"),
    topic: str = typer.Option(..., "--topic"),
    prompt_version: str = typer.Option("h15-v1", "--prompt-version"),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model"),
    window_days: int = typer.Option(NVD_DEFAULT_WINDOW_DAYS, "--window-days"),
    timeline_path: Path = typer.Option(
        None,
        "--timeline",
        help="Path to timeline.yaml. Defaults to data/nj-drones/timeline.yaml.",
    ),
    narratives_path: Path = typer.Option(
        None,
        "--narratives",
        help=(
            "Path to narratives.yaml. Defaults to the nj-drones walk-up loaded at "
            "import time. Pass an explicit path to score a different corpus against "
            "its own narrative definitions."
        ),
    ),
) -> None:
    """Run all four Sensemaking Quality Metrics against the corpus.

    Computes contradicting evidence lag, composite capture risk,
    evidence-narrative alignment, and premature closure resistance.
    Requires IVI, NVD, and SIG to have been computed first.

    Example:
        signals compute eval --corpus nj-drones-2026-04-08 --topic nj-drones
    """
    load_env()

    # Resolve timeline path
    if timeline_path is None:
        here = Path.cwd()
        for parent in (here, *here.parents):
            candidate = parent / "data" / "nj-drones" / "timeline.yaml"
            if candidate.exists():
                timeline_path = candidate
                break
        if timeline_path is None:
            console.print("[red]Cannot find timeline.yaml[/red]. Pass --timeline.")
            raise typer.Exit(code=1)

    console.print("[cyan]Loading data for SQM evaluation[/cyan]")
    console.print(f"  Timeline: {timeline_path}")

    timeline_events = load_timeline_from_yaml(timeline_path)
    console.print(f"  {len(timeline_events)} timeline events")

    # Load corpus documents and hypothesis scores
    raw_docs, raw_scores = load_corpus_documents_for_nvd(
        corpus_version,
        prompt_version=prompt_version,
        model=model,
    )
    if not raw_docs:
        console.print(f"[red]No documents in corpus[/red] {corpus_version}")
        raise typer.Exit(code=1)

    nvd_docs = [
        NvdDocument(
            document_id=d.document_id,
            published_at=d.published_at,
            title=d.title,
            url=d.url,
        )
        for d in raw_docs
    ]
    h_scores = [
        HypothesisScore(
            document_id=s.document_id,
            hypothesis_id=s.hypothesis_id,
            score=s.score,
        )
        for s in raw_scores
    ]

    console.print(f"  {len(nvd_docs)} documents, {len(h_scores)} hypothesis scores")

    # Load precomputed signals
    ivi_rows = load_ivi_series(topic=topic, window_days=EVAL_IVI_WINDOW_DAYS)
    nvd_rows = load_nvd_series(topic=topic, corpus_version=corpus_version, window_days=window_days)
    indep_rows = load_independence_rows(topic=topic, corpus_version=corpus_version)

    console.print(
        f"  {len(ivi_rows)} IVI points, {len(nvd_rows)} NVD points, {len(indep_rows)} SIG rows"
    )

    # -----------------------------------------------------------------------
    # 1. Contradicting evidence lag
    # -----------------------------------------------------------------------

    console.print("\n[bold]1. Contradicting Evidence Lag[/bold]")

    narrative_defs = _resolve_narrative_defs(narratives_path)
    lag_results = compute_contradicting_evidence_lag(
        timeline_events,
        nvd_docs,
        h_scores,
        narrative_defs=narrative_defs,
    )

    if lag_results:
        lag_table = Table(title="Contradicting Evidence Lag")
        lag_table.add_column("Event", style="cyan")
        lag_table.add_column("Narrative")
        lag_table.add_column("Event date", justify="right")
        lag_table.add_column("First contradiction", justify="right")
        lag_table.add_column("Lag (hours)", justify="right", style="bold")
        lag_table.add_column("Contradicting doc")
        lag_table.add_column("H-score", justify="right")

        for r in lag_results:
            lag_table.add_row(
                r.event_id,
                r.narrative_slug,
                r.event_date.isoformat(),
                r.first_contradicting_date.isoformat() if r.first_contradicting_date else "—",
                f"{r.lag_hours:.0f}" if r.lag_hours is not None else "—",
                (r.contradicting_doc_title or "—")[:60],
                f"{r.contradicting_doc_score:.2f}"
                if r.contradicting_doc_score is not None
                else "—",
            )
        console.print(lag_table)
    else:
        console.print("  No narrative-claim events in timeline.")

    # -----------------------------------------------------------------------
    # 2. Composite narrative-capture risk
    # -----------------------------------------------------------------------

    console.print("\n[bold]2. Composite Narrative-Capture Risk[/bold]")

    ivi_points = [
        IviPoint(
            window_end=r["window_end"].date()
            if hasattr(r["window_end"], "date")
            else r["window_end"],
            ivi_value=float(r["value"]),
        )
        for r in ivi_rows
    ]
    nvd_points = [
        NvdPoint(
            narrative_slug=r["narrative_slug"],
            window_start=r["window_start"],
            window_end=r["window_end"].date()
            if hasattr(r["window_end"], "date")
            else r["window_end"],
            narrative_velocity=r["narrative_velocity"],
            evidence_velocity=r["evidence_velocity"],
            nvd_value=float(r["nvd_value"]),
        )
        for r in nvd_rows
    ]
    indep_points = [
        EvalIndependenceResult(
            narrative_slug=r["narrative_slug"],
            independence_score=float(r["independence_score"]),
            amplification_ratio=float(r["amplification_ratio"]),
        )
        for r in indep_rows
    ]

    alerts = compute_capture_risk(ivi_points, nvd_points, indep_points)

    if alerts:
        alert_table = Table(title="Narrative-Capture Risk Alerts")
        alert_table.add_column("Date", style="cyan")
        alert_table.add_column("Narrative")
        alert_table.add_column("IVI", justify="right")
        alert_table.add_column("NVD", justify="right")
        alert_table.add_column("Indep. Score", justify="right")
        alert_table.add_column("Amplification", justify="right")
        alert_table.add_column("Risk", justify="right", style="bold red")

        for a in alerts:
            alert_table.add_row(
                a.alert_date.isoformat(),
                a.narrative_slug,
                f"{a.ivi_value:.1f}",
                f"{a.nvd_value:.2f}",
                f"{a.independence_score:.0f}",
                f"{a.amplification_ratio:.1f}×",
                f"{a.risk_score:.2f}",
            )
        console.print(alert_table)
        console.print(f"  [red]{len(alerts)} capture-risk alerts[/red]")
    else:
        console.print("  [green]No capture-risk alerts (all three signals must converge).[/green]")

    # -----------------------------------------------------------------------
    # 3. Evidence-narrative alignment
    # -----------------------------------------------------------------------

    console.print("\n[bold]3. Evidence-Narrative Alignment[/bold]")

    alignment_results = compute_alignment(
        nvd_docs,
        h_scores,
        window_days=window_days,
        narrative_defs=narrative_defs,
    )

    if alignment_results:
        misaligned = [a for a in alignment_results if not a.aligned]
        console.print(
            f"  {len(alignment_results)} windows analyzed, "
            f"[yellow]{len(misaligned)} misaligned[/yellow] "
            f"(loudest narrative ≠ best-supported)"
        )
        if misaligned:
            align_table = Table(title="Misaligned Windows (loudest ≠ best-supported)")
            align_table.add_column("Date", style="cyan")
            align_table.add_column("Loudest")
            align_table.add_column("Best-supported")
            align_table.add_column("Rho", justify="right")
            for a in misaligned[:15]:
                align_table.add_row(
                    a.window_date.isoformat(),
                    a.loudest_narrative,
                    a.best_supported_narrative,
                    f"{a.rank_correlation:.3f}",
                )
            console.print(align_table)

    # -----------------------------------------------------------------------
    # 4. Premature closure resistance
    # -----------------------------------------------------------------------

    console.print("\n[bold]4. Premature Closure Resistance[/bold]")

    distributions = load_daily_distributions(
        topic=topic,
        corpus_version=corpus_version,
        prompt_version=prompt_version,
        model=model,
    )

    if distributions:
        closure_results = compute_closure_resistance(distributions)
        min_r = min(closure_results, key=lambda c: c.resistance_ratio)
        max_r = max(closure_results, key=lambda c: c.resistance_ratio)
        mean_r = sum(c.resistance_ratio for c in closure_results) / len(closure_results)

        console.print(f"  {len(closure_results)} days analyzed")
        console.print(
            f"  Min resistance: [bold]{min_r.resistance_ratio:.1%}[/bold] "
            f"on {min_r.day} ({min_r.entropy_bits:.3f} bits)"
        )
        console.print(
            f"  Max resistance: [bold]{max_r.resistance_ratio:.1%}[/bold] "
            f"on {max_r.day} ({max_r.entropy_bits:.3f} bits)"
        )
        console.print(f"  Mean resistance: [bold]{mean_r:.1%}[/bold]")
        console.print(f"  Max possible entropy: {closure_results[0].max_entropy_bits:.3f} bits")

        below_70 = [c for c in closure_results if c.resistance_ratio < 0.70]
        if below_70:
            console.print(f"  [yellow]{len(below_70)} days below 70% resistance[/yellow]")
        else:
            console.print(
                "  [green]No days below 70% resistance. Premature closure not detected.[/green]"
            )
    else:
        console.print("  [yellow]No hypothesis distributions found. Run Phase C first.[/yellow]")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    console.print("\n[bold]Summary[/bold]")

    if lag_results:
        same_day = [r for r in lag_results if r.lag_hours is not None and r.lag_hours == 0]
        within_24h = [r for r in lag_results if r.lag_hours is not None and r.lag_hours <= 24]
        console.print(
            f"  Contradicting evidence: {len(same_day)} same-day, "
            f"{len(within_24h)} within 24h, "
            f"out of {len(lag_results)} narrative-claim events"
        )

    if alerts:
        alert_dates = sorted(set(a.alert_date for a in alerts))
        console.print(f"  Capture-risk alerts on: {', '.join(d.isoformat() for d in alert_dates)}")

    if alignment_results:
        console.print(f"  Alignment: {len(misaligned)}/{len(alignment_results)} windows misaligned")

    if distributions:
        console.print(
            f"  Closure resistance: floor {min_r.resistance_ratio:.1%}, mean {mean_r:.1%}"
        )


# ---------------------------------------------------------------------------
# Prescriptive Advisories
# ---------------------------------------------------------------------------


def _find_controllers_yaml_path(topic: str) -> Path | None:
    """Find controllers.yaml for a topic by walking up from CWD.

    Looks for data/{topic}/controllers.yaml, matching how narratives.yaml
    and other topic-specific data files are organized. Falls back to None
    if no match is found, requiring the user to pass --controllers.
    """
    here = Path.cwd()
    for parent in (here, *here.parents):
        candidate = parent / "data" / topic / "controllers.yaml"
        if candidate.exists():
            return candidate
    return None


@app.command("advisories")
def advisories_cmd(
    corpus_version: str = typer.Option(..., "--corpus"),
    topic: str = typer.Option(..., "--topic"),
    prompt_version: str = typer.Option("h15-v1", "--prompt-version"),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model"),
    window_days: int = typer.Option(NVD_DEFAULT_WINDOW_DAYS, "--window-days"),
    ivi_window_days: int = typer.Option(
        IVI_DEFAULT_WINDOW_DAYS,
        "--ivi-window-days",
        help=(
            "IVI window width to load "
            "(must match what was used for `signals compute ivi`). Default 7."
        ),
    ),
    controllers_path: Path | None = typer.Option(
        None,
        "--controllers",
        help="Path to controllers.yaml. Defaults to data/nj-drones/controllers.yaml.",
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Generate prescriptive advisories from current signal state.

    Maps STAMP diagnostic signals (IVI, NVD, SIG) to recommended control
    actions for specific institutional controllers. Requires IVI, NVD, SIG,
    and hypothesis distributions to have been computed first.

    Example:
        signals compute advisories --corpus nj-drones-2026-04-09 --topic nj-drones
    """
    load_env()

    # Resolve controllers.yaml
    if controllers_path is None:
        controllers_path = _find_controllers_yaml_path(topic)
    if controllers_path is None or not controllers_path.exists():
        console.print(
            "[red]Cannot find controllers.yaml[/red]. "
            "Pass --controllers or run from the dev/tell/ directory."
        )
        raise typer.Exit(code=1)

    console.print(f"[cyan]Loading controllers[/cyan] from {controllers_path}")
    controller_defs = load_controllers_yaml(controllers_path)
    console.print(f"  {len(controller_defs)} controllers loaded")

    # Load all precomputed signals
    console.print(f"[cyan]Loading precomputed signals[/cyan] for {topic}")

    ivi_rows = load_ivi_series(topic=topic, window_days=ivi_window_days)
    nvd_rows = load_nvd_series(
        topic=topic,
        corpus_version=corpus_version,
        window_days=window_days,
    )
    indep_rows = load_independence_rows(topic=topic, corpus_version=corpus_version)
    distributions = load_daily_distributions(
        topic=topic,
        corpus_version=corpus_version,
        prompt_version=prompt_version,
        model=model,
    )

    console.print(
        f"  {len(ivi_rows)} IVI points, {len(nvd_rows)} NVD points, "
        f"{len(indep_rows)} SIG rows, {len(distributions)} entropy days"
    )

    # Convert to prescribe.py input types
    ivi_points = [
        IviPoint(
            window_end=(
                r["window_end"].date() if hasattr(r["window_end"], "date") else r["window_end"]
            ),
            ivi_value=float(r["value"]),
        )
        for r in ivi_rows
    ]

    nvd_snapshots = [
        NvdSnapshot(
            narrative_slug=str(r["narrative_slug"]),
            window_end=(
                r["window_end"].date() if hasattr(r["window_end"], "date") else r["window_end"]
            ),
            nvd_value=float(r["nvd_value"]),
            narrative_velocity=int(r["narrative_velocity"]),
            evidence_velocity=int(r["evidence_velocity"]),
        )
        for r in nvd_rows
    ]

    sig_snapshots = [
        SigSnapshot(
            narrative_slug=str(r["narrative_slug"]),
            independence_score=float(r["independence_score"]),
            amplification_ratio=float(r["amplification_ratio"]),
            origin_label=str(r.get("origin_label", "unknown")),
        )
        for r in indep_rows
    ]

    # Compute capture-risk alerts (reuse eval logic)
    nvd_points_for_risk = [
        NvdPoint(
            narrative_slug=str(r["narrative_slug"]),
            window_start=r["window_start"],
            window_end=(
                r["window_end"].date() if hasattr(r["window_end"], "date") else r["window_end"]
            ),
            narrative_velocity=int(r["narrative_velocity"]),
            evidence_velocity=int(r["evidence_velocity"]),
            nvd_value=float(r["nvd_value"]),
        )
        for r in nvd_rows
    ]
    indep_for_risk = [
        EvalIndependenceResult(
            narrative_slug=str(r["narrative_slug"]),
            independence_score=float(r["independence_score"]),
            amplification_ratio=float(r["amplification_ratio"]),
        )
        for r in indep_rows
    ]
    # Bound IVI points to the NVD date range before composite risk computation.
    # signal_ivi is intentionally not corpus-versioned at the schema level
    # (its unique key is (topic, window_end) with no corpus_version column),
    # so load_ivi_series returns whatever IVI values were last written for
    # the topic regardless of which corpus is currently being scored. That
    # is fine for the IVI-only advisory path, which is inherently topic-
    # scoped. It is not fine for composite capture-risk alerts, which must
    # be reproducible against a specific corpus. Filtering to the NVD date
    # range is the pragmatic defense: NVD is corpus-filtered at load time,
    # so its window_ends bound the temporal coverage of the active corpus.
    if nvd_points_for_risk:
        nvd_start = min(p.window_end for p in nvd_points_for_risk)
        nvd_end = max(p.window_end for p in nvd_points_for_risk)
        ivi_points_for_risk = [p for p in ivi_points if nvd_start <= p.window_end <= nvd_end]
    else:
        ivi_points_for_risk = []
    capture_alerts = compute_capture_risk(ivi_points_for_risk, nvd_points_for_risk, indep_for_risk)

    # Entropy snapshots
    entropy_snapshots = []
    if distributions:
        from .constants import MAX_ENTROPY_BITS

        max_entropy = MAX_ENTROPY_BITS
        for d in distributions:
            day = d["day"]
            if isinstance(day, str):
                from datetime import date as _date

                day = _date.fromisoformat(day)
            entropy = float(d.get("entropy_bits", 0.0))
            entropy_snapshots.append(
                EntropySnapshot(
                    day=day,
                    entropy_bits=entropy,
                    resistance_ratio=entropy / max_entropy if max_entropy > 0 else 0.0,
                    modal_hypothesis=str(d.get("modal_hypothesis", "")),
                )
            )

    # Determine a SIG advisory date (use the last IVI date or today)
    sig_date = None
    if ivi_points:
        sig_date = max(p.window_end for p in ivi_points)

    # Generate advisories
    console.print("\n[cyan]Generating prescriptive advisories...[/cyan]")

    all_advisories = generate_advisories(
        controller_defs,
        ivi_series=ivi_points,
        nvd_points=nvd_snapshots,
        sig_results=sig_snapshots,
        capture_alerts=capture_alerts,
        entropy_points=entropy_snapshots,
        sig_advisory_date=sig_date,
    )

    console.print(f"[green]Generated {len(all_advisories)} advisories[/green]")

    if not all_advisories:
        console.print("[yellow]No signal conditions exceeded thresholds.[/yellow]")
        return

    # Summary by severity
    from collections import Counter

    severity_counts = Counter(a.severity for a in all_advisories)
    trigger_counts = Counter(a.signal_trigger for a in all_advisories)
    controller_counts = Counter(a.controller_slug for a in all_advisories)

    summary = Table(title="Advisory Summary")
    summary.add_column("Dimension", style="cyan")
    summary.add_column("Breakdown")
    summary.add_row(
        "By severity",
        ", ".join(f"{k}: {v}" for k, v in sorted(severity_counts.items())),
    )
    summary.add_row(
        "By trigger",
        ", ".join(f"{k}: {v}" for k, v in sorted(trigger_counts.items())),
    )
    summary.add_row(
        "By controller",
        ", ".join(f"{k}: {v}" for k, v in sorted(controller_counts.items())),
    )
    console.print(summary)

    # Show alert-severity advisories in detail
    alerts_only = [a for a in all_advisories if a.severity == "alert"]
    if alerts_only:
        alert_table = Table(title=f"Alert-Severity Advisories ({len(alerts_only)})")
        alert_table.add_column("Date", style="cyan")
        alert_table.add_column("Controller")
        alert_table.add_column("Trigger")
        alert_table.add_column("Narrative")
        alert_table.add_column("STAMP Failure")
        alert_table.add_column("Recommendation", max_width=60)

        for a in alerts_only[:20]:
            alert_table.add_row(
                a.advisory_date.isoformat(),
                a.controller_slug,
                a.signal_trigger,
                a.narrative_slug or "—",
                a.stamp_failure_mode,
                a.recommendation[:60] + "..." if len(a.recommendation) > 60 else a.recommendation,
            )
        console.print(alert_table)

    if dry_run:
        console.print("[yellow]Dry run; not persisting to Neon.[/yellow]")
        return

    # Persist
    rows_to_upsert = [
        {
            "controller_slug": a.controller_slug,
            "narrative_slug": a.narrative_slug,
            "signal_trigger": a.signal_trigger,
            "signal_values": a.signal_values,
            "advisory_type": a.advisory_type,
            "severity": a.severity,
            "recommendation": a.recommendation,
            "rationale": a.rationale,
            "klein_activity": a.klein_activity,
            "stamp_failure_mode": a.stamp_failure_mode,
            "advisory_date": a.advisory_date,
        }
        for a in all_advisories
    ]
    affected = upsert_advisory_rows(
        topic=topic,
        corpus_version=corpus_version,
        rows=rows_to_upsert,
    )
    console.print(f"[green]Upserted {affected} advisory rows to Neon[/green]")


@app.command("advisories-status")
def advisories_status(
    topic: str = typer.Option(..., "--topic"),
    corpus_version: str | None = typer.Option(None, "--corpus", help="Filter by corpus version"),
    controller: str | None = typer.Option(None, "--controller", help="Filter by controller slug"),
    severity: str | None = typer.Option(None, "--severity", help="Filter by severity"),
) -> None:
    """Show persisted advisories for a topic.

    Without --corpus, shows advisories from all corpus versions (useful for
    cross-corpus comparison). With --corpus, shows only advisories generated
    from that specific corpus snapshot.
    """
    load_env()

    rows = load_advisories(
        topic=topic,
        corpus_version=corpus_version,
        controller_slug=controller,
        severity=severity,
    )
    if not rows:
        label = f"{topic}" + (f" ({corpus_version})" if corpus_version else "")
        console.print(f"[yellow]No advisories for {label}[/yellow]")
        return

    title_suffix = f", {corpus_version}" if corpus_version else ", all corpus versions"
    table = Table(title=f"Advisories for {topic}{title_suffix} ({len(rows)} total)")
    table.add_column("Date", style="cyan")
    table.add_column("Corpus")
    table.add_column("Severity", justify="center")
    table.add_column("Controller")
    table.add_column("Trigger")
    table.add_column("Narrative")
    table.add_column("Type")
    table.add_column("STAMP Failure")

    for r in rows:
        sev = str(r["severity"])
        sev_style = {"alert": "[bold red]", "advisory": "[yellow]", "watch": "[dim]"}.get(sev, "")
        sev_end = {"alert": "[/bold red]", "advisory": "[/yellow]", "watch": "[/dim]"}.get(sev, "")

        table.add_row(
            r["advisory_date"].date().isoformat()
            if hasattr(r["advisory_date"], "date")
            else str(r["advisory_date"]),
            str(r.get("corpus_version", "—")),
            f"{sev_style}{sev}{sev_end}",
            str(r["controller_slug"]),
            str(r["signal_trigger"]),
            str(r.get("narrative_slug") or "—"),
            str(r["advisory_type"]),
            str(r["stamp_failure_mode"]),
        )
    console.print(table)
