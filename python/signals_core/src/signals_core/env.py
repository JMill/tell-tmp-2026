"""Environment loading for TELL pipeline CLIs.

Every Typer CLI in the pipeline needs the same thing: find the nearest
`.env.local`, load it with `python-dotenv`, and continue. Three identical
copies of this function previously lived in signals_ingest, signals_analyze,
and signals_methods. They live here now.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_env(start: Path | None = None, filename: str = ".env.local") -> Path | None:
    """Find the nearest ``filename`` walking up from ``start`` and load it.

    Parameters
    ----------
    start:
        Directory to start the search from. Defaults to ``Path.cwd()``.
    filename:
        Env file name to look for. Defaults to ``.env.local``.

    Returns
    -------
    The path that was loaded, or ``None`` if no env file was found. Callers
    that require an env file should check the return value; callers that
    simply want best-effort loading can ignore it.
    """
    here = start if start is not None else Path.cwd()
    for parent in (here, *here.parents):
        candidate = parent / filename
        if candidate.exists():
            load_dotenv(candidate)
            return candidate
    return None
