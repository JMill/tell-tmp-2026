"""Typer CLI for signals_ingest subcommands.

Exposed via the top-level `signals ingest ...` CLI aggregator in signals_cli.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from signals_core import load_env, make_pipeline_progress, make_summary_table

from signals_ingest.adapters import direct as direct_adapter
from signals_ingest.adapters import wayback as wayback_adapter
from signals_ingest.batch import load_seed_file, run_batch
from signals_ingest.storage import document_count

console = Console()
app = typer.Typer(
    name="ingest",
    help="Fetch documents from source adapters.",
    no_args_is_help=True,
    add_completion=False,
)


def _render_single_result(result: object, title: str = "Ingested Document") -> None:
    """Render a single IngestResult as a Rich table."""
    table = make_summary_table(title)
    table.add_row("Document ID", getattr(result, "document_id", ""))
    table.add_row("Source ID", getattr(result, "source_id", ""))
    table.add_row("Title", getattr(result, "title", None) or "(no title)")
    table.add_row("Extracted chars", str(getattr(result, "text_char_count", "")))
    blob = getattr(result, "blob_result", None)
    if blob is not None:
        table.add_row("Blob URL", getattr(blob, "url", ""))
        table.add_row("Blob size (bytes)", str(getattr(blob, "size", "")))
    console.print(table)


@app.command()
def wayback(
    url: str = typer.Option(..., "--url", help="Original URL to fetch from the Wayback Machine"),
    corpus_version: str = typer.Option(
        "nj-drones-2026-04-07",
        "--corpus",
        help="Corpus version label",
    ),
    timestamp: str | None = typer.Option(
        None,
        "--timestamp",
        help="Wayback timestamp (YYYYMMDDHHMMSS) to pin the snapshot",
    ),
) -> None:
    """Ingest a single URL via the Wayback Machine.

    Example:
        signals ingest wayback --url https://www.nytimes.com/2024/12/12/us/drones.html
    """
    load_env()

    console.print(f"[cyan]Resolving Wayback snapshot for[/cyan] {url}")
    try:
        result = wayback_adapter.ingest_url(
            url=url,
            corpus_version=corpus_version,
            timestamp=timestamp,
        )
    except Exception as exc:
        console.print(f"[red]Ingestion failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    _render_single_result(result)


@app.command()
def direct(
    url: str = typer.Option(..., "--url", help="URL to fetch directly from the live web"),
    corpus_version: str = typer.Option(
        "nj-drones-2026-04-07",
        "--corpus",
        help="Corpus version label",
    ),
    source_kind: str | None = typer.Option(
        None,
        "--source-kind",
        help="Override the inferred source kind (gov, news, social, etc.)",
    ),
) -> None:
    """Ingest a single URL via a direct HTTP fetch (no Wayback).

    Use for government press releases, stable institutional URLs, or any
    source that is still live and authoritative. For retrospective research
    where point-in-time integrity matters, prefer `signals ingest wayback`.
    """
    load_env()

    console.print(f"[cyan]Fetching[/cyan] {url}")
    try:
        result = direct_adapter.ingest_url(
            url=url,
            corpus_version=corpus_version,
            source_kind=source_kind,
        )
    except Exception as exc:
        console.print(f"[red]Ingestion failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    _render_single_result(result)


@app.command()
def batch(
    corpus_version: str = typer.Option(
        ...,
        "--corpus",
        help="Corpus version label to write all documents under",
    ),
    seeds_path: Path = typer.Option(
        ...,
        "--seeds",
        help="Path to a seed-urls.yaml file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
) -> None:
    """Ingest every URL in a seed-urls.yaml file into a single corpus.

    Dispatches each entry to the Wayback or direct adapter based on its
    `adapter` field. Failures are isolated per entry — the batch continues
    after any single failure and a summary at the end lists successes and
    failures with enough detail to re-run individual entries.

    Example:
        signals ingest batch --corpus nj-drones-2026-04-08 --seeds data/nj-drones/seed-urls.yaml
    """
    load_env()

    console.print(f"[cyan]Loading seeds from[/cyan] {seeds_path}")
    try:
        seeds = load_seed_file(seeds_path)
    except Exception as exc:
        console.print(f"[red]Failed to load seed file:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[cyan]Running batch ingest[/cyan] corpus={corpus_version} entries={len(seeds)}")

    progress = make_pipeline_progress(console)

    with progress:
        task_id = progress.add_task("Ingesting", total=len(seeds))

        def _tick(i: int, total: int, entry: object, result_or_exc: object) -> None:
            is_err = isinstance(result_or_exc, BaseException)
            url = getattr(entry, "url", "")
            short = url if len(url) <= 70 else url[:67] + "..."
            if is_err:
                console.print(f"  [red]✗[/red] {short}  {type(result_or_exc).__name__}")
            else:
                console.print(f"  [green]✓[/green] {short}")
            progress.update(task_id, advance=1)

        summary = run_batch(
            seeds=seeds,
            corpus_version=corpus_version,
            seeds_path=str(seeds_path),
            on_progress=_tick,
        )

    # Render final summary
    table = make_summary_table("Batch Summary")
    table.add_row("Corpus", corpus_version)
    table.add_row("Seeds file", str(seeds_path))
    table.add_row("Total", str(summary.total))
    table.add_row("Succeeded", f"[green]{summary.succeeded}[/green]")
    table.add_row("Failed", f"[red]{summary.failed}[/red]" if summary.failed else "0")
    console.print(table)

    if summary.failures:
        console.print("\n[red]Failures:[/red]")
        for url, err in summary.failures:
            console.print(f"  - {url}")
            console.print(f"    [red]{err}[/red]")

    # Fail the command on ANY partial failure. The pipeline exists to validate
    # empirical claims — a batch with silently-dropped URLs is a scientific
    # liability, not a convenience. Automated runs and smoke tests need to see
    # the non-zero exit so they can retry, alert, or block downstream phases.
    # The summary table is already printed above, so operators can see what
    # succeeded before the exit.
    if summary.failed > 0:
        raise typer.Exit(code=1)


@app.command()
def status(
    corpus_version: str | None = typer.Option(
        None,
        "--corpus",
        help="Filter by corpus version",
    ),
) -> None:
    """Show current corpus status (document counts)."""
    load_env()
    count = document_count(corpus_version)
    label = corpus_version or "all corpora"
    console.print(f"[green]{count}[/green] documents in {label}")
