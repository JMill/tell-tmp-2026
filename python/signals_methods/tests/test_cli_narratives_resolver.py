"""End-to-end tests for the CLI-side narratives resolver wrapper.

Exercises the `_resolve_narrative_defs` helper that all three compute
commands (nvd, independence, eval) route through. The wrapper's contract
is that any malformed or missing --narratives input produces a controlled
typer.Exit rather than an unhandled traceback. These tests guard that
contract against silent regressions when the loader's exception surface
changes.

Run with: uv run pytest python/signals_methods/tests/test_cli_narratives_resolver.py
"""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
from signals_methods.cli import _resolve_narrative_defs


def test_resolver_controlled_exit_on_missing_file(tmp_path: Path) -> None:
    """A nonexistent --narratives path exits with typer.Exit code 1."""
    with pytest.raises(typer.Exit) as excinfo:
        _resolve_narrative_defs(tmp_path / "does-not-exist.yaml")
    assert excinfo.value.exit_code == 1


def test_resolver_controlled_exit_on_empty_file(tmp_path: Path) -> None:
    """An empty --narratives file exits with typer.Exit, not AttributeError."""
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    with pytest.raises(typer.Exit) as excinfo:
        _resolve_narrative_defs(empty)
    assert excinfo.value.exit_code == 1


def test_resolver_controlled_exit_on_non_mapping_root(tmp_path: Path) -> None:
    """A YAML file whose root is a list exits with typer.Exit."""
    bad = tmp_path / "bad-root.yaml"
    bad.write_text("- a\n- b\n")
    with pytest.raises(typer.Exit) as excinfo:
        _resolve_narrative_defs(bad)
    assert excinfo.value.exit_code == 1


def test_resolver_controlled_exit_on_non_list_narratives(tmp_path: Path) -> None:
    """A 'narratives' key that is a mapping rather than a list exits with
    typer.Exit."""
    bad = tmp_path / "bad-narratives.yaml"
    bad.write_text("narratives:\n  slug: foo\n  keywords: [a, b]\n")
    with pytest.raises(typer.Exit) as excinfo:
        _resolve_narrative_defs(bad)
    assert excinfo.value.exit_code == 1


def test_resolver_controlled_exit_on_directory_path(tmp_path: Path) -> None:
    """Passing a directory (common typo: forgetting /narratives.yaml) must
    surface as typer.Exit rather than a raw IsADirectoryError traceback.

    IsADirectoryError is an OSError subclass; Python can also raise
    PermissionError (another OSError subclass) for unreadable files.
    The resolver must convert both into a clean user-facing error."""
    subdir = tmp_path / "a-directory"
    subdir.mkdir()
    with pytest.raises(typer.Exit) as excinfo:
        _resolve_narrative_defs(subdir)
    assert excinfo.value.exit_code == 1


def test_resolver_loads_valid_narratives(tmp_path: Path) -> None:
    """A well-formed minimal --narratives file returns the loaded defs."""
    valid = tmp_path / "minimal.yaml"
    valid.write_text(
        "narratives:\n"
        "  - slug: test-narrative\n"
        "    hypothesis_id: H1\n"
        "    keywords: [foo, bar]\n"
        "    label: Test Narrative\n"
    )
    defs = _resolve_narrative_defs(valid)
    assert len(defs) == 1
    assert defs[0]["slug"] == "test-narrative"
