"""Rich console helpers shared across TELL CLIs.

Two patterns recur across every pipeline CLI: a progress bar with the same
four-column layout (description, bar, "n/total", elapsed), and a
two-column summary table with ``show_header=False``. Those live here so
adding a new CLI does not mean copying another copy of the ctor.
"""

from __future__ import annotations

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table


def make_pipeline_progress(console: Console, *, transient: bool = False) -> Progress:
    """Return a pre-configured Rich ``Progress`` for pipeline CLIs.

    Columns: task description, bar, ``completed/total`` counter, elapsed
    time. The caller owns the returned object and is expected to use it as
    a context manager.
    """
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=transient,
    )


def make_summary_table(title: str, *, field_style: str = "cyan") -> Table:
    """Return a 2-column (Field, Value) Rich ``Table`` with no header.

    Used by every CLI to render a small summary: corpus label, counts,
    token totals, etc. The column styles match the existing TELL
    conventions exactly so outputs are byte-identical to the ad-hoc
    tables they replace.
    """
    table = Table(title=title, show_header=False)
    table.add_column("Field", style=field_style)
    table.add_column("Value")
    return table
