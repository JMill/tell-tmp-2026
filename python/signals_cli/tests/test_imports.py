"""Import smoke test for the signals CLI entry point.

The `signals` console script imports every subcommand app at startup, so a
missing re-export anywhere in the package graph makes the entire CLI
unlaunchable. PR #40's ruff cleanup removed the `fetch_blob` re-export from
signals_analyze.storage as an unused import, which no test caught because
nothing imported the CLI modules. This test exists so that failure mode is
caught at test time instead of at the terminal.
"""


def test_cli_app_imports() -> None:
    from signals_cli.__main__ import app

    assert app is not None


def test_analyze_storage_reexports_fetch_blob() -> None:
    from signals_analyze.storage import fetch_blob
    from vercel_blob_client import fetch

    assert fetch_blob is fetch
