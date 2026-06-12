"""Typer CLI for signals_analyze subcommands.

Exposed via the top-level `signals analyze ...` CLI aggregator in signals_cli.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from signals_core import load_env, make_pipeline_progress, make_summary_table

from signals_analyze.extract_helpers import extract_from_html
from signals_analyze.hypothesis_scoring import (
    DEFAULT_MODEL,
    HYPOTHESIS_PROMPT_VERSION,
    score_document,
)
from signals_analyze.storage import (
    aggregate_daily_distributions,
    fetch_blob,
    get_scored_document_ids,
    load_corpus_documents,
    load_daily_distributions,
    upsert_daily_distributions,
    upsert_hypothesis_scores,
)

console = Console()
app = typer.Typer(
    name="analyze",
    help="LLM-driven analysis: hypothesis scoring, source reliability, embeddings.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def hypotheses(
    corpus_version: str = typer.Option(
        ...,
        "--corpus",
        help="Corpus version label",
    ),
    topic: str = typer.Option(
        ...,
        "--topic",
        help="Topic identifier (e.g. 'nj-drones')",
    ),
    pilot: int | None = typer.Option(
        None,
        "--pilot",
        help="Score only the first N documents (after skipping already-scored)",
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        help="Anthropic model to use for scoring",
    ),
    prompt_version: str = typer.Option(
        HYPOTHESIS_PROMPT_VERSION,
        "--prompt-version",
        help="Prompt version label. Bumping forks the result set rather than overwriting.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-score documents that already have scores for this prompt+model",
    ),
) -> None:
    """Score every document in a corpus against H1-H5 via Claude tool calls.

    The CLI is resumable by default — documents that already have a score for
    the given (prompt_version, model) are skipped. Pass --force to re-score
    everything (overwrites in place via the unique constraint).

    Cost: ~$0.0007 per document with Haiku 4.5. The 38-doc NJ drones corpus
    is well under $0.10 for a full run.

    Example:
        signals analyze hypotheses --corpus nj-drones-2026-04-08 --topic nj-drones
        signals analyze hypotheses --corpus nj-drones-2026-04-08 --topic nj-drones --pilot 5
    """
    load_env()

    console.print(f"[cyan]Loading corpus[/cyan] {corpus_version}")
    docs = load_corpus_documents(corpus_version)
    if not docs:
        console.print(f"[red]No documents in corpus[/red] {corpus_version}")
        raise typer.Exit(code=1)

    console.print(f"  loaded {len(docs)} documents")

    if not force:
        already_scored = get_scored_document_ids(
            corpus_version=corpus_version,
            prompt_version=prompt_version,
            model=model,
        )
        unscored = [d for d in docs if d.id not in already_scored]
        if already_scored:
            console.print(
                f"  [yellow]skipping {len(already_scored)} already-scored documents[/yellow] "
                f"(pass --force to re-score)"
            )
    else:
        unscored = docs

    if pilot is not None:
        unscored = unscored[:pilot]
        console.print(
            f"  [cyan]pilot mode:[/cyan] scoring first {len(unscored)} unscored documents"
        )

    # When unscored is empty, skip the scoring loop but DO NOT return early.
    # Distributions may still need to be (re)built from existing
    # document_hypothesis_scores — e.g. after a transient failure that occurred
    # after scoring completed but before the upsert, or after a manual table
    # cleanup. Falling through to the distribution gates below is correct.
    if not unscored:
        console.print("[green]Nothing to score; all documents already have scores.[/green]")
        failed = 0
    else:
        console.print(
            f"[cyan]Scoring[/cyan] {len(unscored)} documents with model={model} "
            f"prompt_version={prompt_version}"
        )

        succeeded = 0
        failed = 0
        total_input_tokens = 0
        total_output_tokens = 0
        failures: list[tuple[str, str]] = []

        progress = make_pipeline_progress(console)

        with progress:
            task_id = progress.add_task("Scoring", total=len(unscored))

            for doc in unscored:
                try:
                    if not doc.content_blob_key:
                        raise RuntimeError("document has no content_blob_key")
                    raw_html = fetch_blob(doc.content_blob_key)
                    extracted = extract_from_html(raw_html)
                    scores = score_document(
                        title=extracted.title or doc.title,
                        text=extracted.text,
                        url=doc.url,
                        source_kind=doc.source_kind,
                        model=model,
                    )
                    upsert_hypothesis_scores(
                        document_id=doc.id,
                        scores=scores,
                        model=model,
                        prompt_version=prompt_version,
                    )
                    succeeded += 1
                    total_input_tokens += scores.raw_input_tokens
                    total_output_tokens += scores.raw_output_tokens
                    modal = max(scores.as_dict().keys(), key=lambda k: scores.as_dict()[k])
                    short_url = doc.url if len(doc.url) <= 60 else doc.url[:57] + "..."
                    console.print(
                        f"  [green]✓[/green] {short_url}  "
                        f"modal={modal} "
                        f"H1={scores.h1:.2f} H2={scores.h2:.2f} H3={scores.h3:.2f} "
                        f"H4={scores.h4:.2f} H5={scores.h5:.2f}"
                    )
                except Exception as exc:
                    failed += 1
                    failures.append((doc.url, f"{type(exc).__name__}: {exc}"))
                    short_url = doc.url if len(doc.url) <= 60 else doc.url[:57] + "..."
                    console.print(f"  [red]✗[/red] {short_url}  {type(exc).__name__}")

                progress.update(task_id, advance=1)

        summary = make_summary_table("Scoring Summary")
        summary.add_row("Corpus", corpus_version)
        summary.add_row("Topic", topic)
        summary.add_row("Model", model)
        summary.add_row("Prompt version", prompt_version)
        summary.add_row("Succeeded", f"[green]{succeeded}[/green]")
        summary.add_row("Failed", f"[red]{failed}[/red]" if failed else "0")
        summary.add_row("Input tokens", f"{total_input_tokens:,}")
        summary.add_row("Output tokens", f"{total_output_tokens:,}")
        # Rough cost estimate at Haiku 4.5 published rates ($1/Mtok in, $5/Mtok out)
        cost = total_input_tokens / 1_000_000 + 5 * total_output_tokens / 1_000_000
        summary.add_row("Est. cost (Haiku 4.5)", f"${cost:.4f}")
        console.print(summary)

        if failures:
            console.print("\n[red]Failures:[/red]")
            for url, err in failures:
                console.print(f"  - {url}")
                console.print(f"    [red]{err}[/red]")

        # Gate distribution upserts on full scoring success. If ANY document in
        # this run failed, we must not overwrite the persisted daily distributions
        # with values derived from a partial corpus — doing so would silently
        # corrupt downstream empirical results and make the dashboard show numbers
        # derived from incomplete data. Same reasoning as the batch ingest exit
        # code. The summary table above still prints so operators see the partial
        # result, and the individual document_hypothesis_scores rows that DID
        # succeed remain persisted (they're idempotent and re-runnable).
        if failed > 0:
            console.print(
                f"\n[red]Skipping hypothesis_distributions upsert because "
                f"{failed} document(s) failed in this run.[/red]"
            )
            console.print(
                "[yellow]Re-run the command to retry failures and refresh "
                "distributions once all scoring succeeds.[/yellow]"
            )
            raise typer.Exit(code=1)

    # Gate distribution upserts on full-corpus runs. A --pilot N run scores
    # only the first N documents by design, so `failed == 0` is not sufficient
    # to guarantee complete coverage. Upserting distributions from a pilot run
    # would overwrite stored values with data derived from a partial corpus —
    # the same silent-corruption risk as a partial failure run. Pilot mode is
    # for prompt validation, not for producing canonical distributions.
    if pilot is not None:
        console.print(
            f"\n[yellow]Skipping hypothesis_distributions upsert because "
            f"--pilot {pilot} was used (partial corpus by design).[/yellow]"
        )
        console.print("[yellow]Run without --pilot to produce canonical distributions.[/yellow]")
        return

    console.print("\n[cyan]Aggregating daily hypothesis distributions...[/cyan]")
    distributions = aggregate_daily_distributions(
        corpus_version=corpus_version,
        prompt_version=prompt_version,
        model=model,
    )
    n = upsert_daily_distributions(
        topic=topic,
        corpus_version=corpus_version,
        prompt_version=prompt_version,
        model=model,
        distributions=distributions,
    )
    console.print(f"[green]Persisted {n} daily distribution rows[/green]")

    if distributions:
        # Show the top entries by entropy and the modal hypothesis evolution
        dist_table = Table(title=f"Daily distributions for {topic}")
        dist_table.add_column("Day", style="cyan")
        dist_table.add_column("Docs", justify="right")
        dist_table.add_column("Modal", justify="center")
        dist_table.add_column("Modal P", justify="right")
        dist_table.add_column("Entropy (bits)", justify="right")
        dist_table.add_column("H1", justify="right")
        dist_table.add_column("H2", justify="right")
        dist_table.add_column("H3", justify="right")
        dist_table.add_column("H4", justify="right")
        dist_table.add_column("H5", justify="right")
        for d in distributions:
            dist_table.add_row(
                d.day.isoformat(),
                str(d.document_count),
                d.modal_hypothesis,
                f"{d.modal_probability:.2f}",
                f"{d.entropy:.2f}",
                f"{d.distribution['H1']:.2f}",
                f"{d.distribution['H2']:.2f}",
                f"{d.distribution['H3']:.2f}",
                f"{d.distribution['H4']:.2f}",
                f"{d.distribution['H5']:.2f}",
            )
        console.print(dist_table)

    # If we reach here: failed == 0 and pilot is None — full-corpus success.


@app.command("hypotheses-status")
def hypotheses_status(
    topic: str = typer.Option(..., "--topic", help="Topic identifier"),
    corpus_version: str = typer.Option(..., "--corpus", help="Corpus version label"),
    model: str = typer.Option(DEFAULT_MODEL, "--model"),
    prompt_version: str = typer.Option(HYPOTHESIS_PROMPT_VERSION, "--prompt-version"),
) -> None:
    """Show the persisted daily hypothesis distributions for a topic and corpus."""
    load_env()

    rows = load_daily_distributions(
        topic=topic, corpus_version=corpus_version, prompt_version=prompt_version, model=model
    )
    if not rows:
        console.print(
            f"[yellow]No distributions for topic {topic} corpus {corpus_version}[/yellow]"
        )
        return

    table = Table(title=f"Daily hypothesis distributions for {topic} ({corpus_version})")
    table.add_column("Day", style="cyan")
    table.add_column("Docs", justify="right")
    table.add_column("Modal", justify="center")
    table.add_column("Modal P", justify="right")
    table.add_column("Entropy", justify="right")
    table.add_column("H1", justify="right")
    table.add_column("H2", justify="right")
    table.add_column("H3", justify="right")
    table.add_column("H4", justify="right")
    table.add_column("H5", justify="right")
    for row in rows:
        d = row["distribution"]
        table.add_row(
            row["day"].date().isoformat(),
            str(row["document_count"]),
            row["modal_hypothesis"],
            f"{row['modal_probability']:.2f}",
            f"{row['entropy']:.2f}",
            f"{d.get('H1', 0):.2f}",
            f"{d.get('H2', 0):.2f}",
            f"{d.get('H3', 0):.2f}",
            f"{d.get('H4', 0):.2f}",
            f"{d.get('H5', 0):.2f}",
        )
    console.print(table)
    console.print(f"Total rows: {len(rows)}")
