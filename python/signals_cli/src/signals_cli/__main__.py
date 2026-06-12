"""Signals CLI entry point.

Aggregates subcommands from the other signals_* packages.
"""

from __future__ import annotations

import typer
from rich.console import Console

# Subcommand apps are imported from each package so they appear under this CLI.
from signals_analyze.cli import app as analyze_app
from signals_ingest.cli import app as ingest_app
from signals_methods.cli import app as compute_app

console = Console()

app = typer.Typer(
    name="signals",
    help="OSINT weak signal detection pipeline CLI.",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(ingest_app, name="ingest", help="Fetch documents from source adapters")
app.add_typer(compute_app, name="compute", help="Compute novel weak signal methods over corpora")
app.add_typer(analyze_app, name="analyze", help="LLM-driven analysis (hypothesis scoring, etc.)")


@app.command()
def version() -> None:
    """Print the CLI version."""
    console.print("signals 0.1.0")


if __name__ == "__main__":
    app()
