"""Unit tests for the narrative-defs loader.

These tests cover:
- The public `load_narrative_defs(path)` function with a real YAML fixture.
- Hypothesis-id normalization (H4-foreign → H4) across arbitrary topics.
- Rich-metadata preservation (label, originating_source) pass-through.
- Resolver behavior when the topic's data/{topic}/narratives.yaml exists on
  the walk-up path.
- The module-level NARRATIVE_DEFS default remains populated (nj-drones).

Run with: uv run pytest python/signals_methods/tests/test_narratives_loader.py
"""

from __future__ import annotations

from pathlib import Path

import pytest
from signals_methods.constants import (
    NARRATIVE_DEFS,
    find_narratives_yaml,
    load_narrative_defs,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Return the dev/tell/ root (two up from python/signals_methods/tests)."""
    return Path(__file__).resolve().parents[3]


def _nj_drones_yaml() -> Path:
    return _repo_root() / "data" / "nj-drones" / "narratives.yaml"


def _high_altitude_yaml() -> Path:
    return _repo_root() / "data" / "high-altitude-objects-2023" / "narratives.yaml"


# ---------------------------------------------------------------------------
# Loader behavior
# ---------------------------------------------------------------------------


def test_load_narrative_defs_returns_list_of_dicts() -> None:
    defs = load_narrative_defs(_nj_drones_yaml())
    assert isinstance(defs, list)
    assert all(isinstance(d, dict) for d in defs)
    assert len(defs) > 0


def test_load_narrative_defs_normalizes_hypothesis_subtype() -> None:
    """H4-foreign, H3-benign, etc. must be collapsed to their base H1-H5 bucket."""
    defs = load_narrative_defs(_nj_drones_yaml())
    for d in defs:
        h = d["hypothesis"]
        assert h in {"H1", "H2", "H3", "H4", "H5", ""}, (
            f"Narrative {d['slug']!r} has non-base hypothesis {h!r}. Loader must strip subtypes."
        )


def test_load_narrative_defs_preserves_rich_metadata() -> None:
    defs = load_narrative_defs(_nj_drones_yaml())
    sample = defs[0]
    assert "slug" in sample
    assert "keywords" in sample
    assert "label" in sample
    assert "originating_source" in sample


def test_load_narrative_defs_accepts_str_and_path() -> None:
    """Callers may pass either `str` or `pathlib.Path`. Both must work."""
    from_path = load_narrative_defs(_nj_drones_yaml())
    from_str = load_narrative_defs(str(_nj_drones_yaml()))
    assert from_path == from_str


def test_load_narrative_defs_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_narrative_defs(_repo_root() / "data" / "not-a-topic" / "narratives.yaml")


def test_load_narrative_defs_high_altitude_differs_from_nj_drones() -> None:
    """Regression guard: loading a non-default topic must produce different defs
    than the nj-drones default. If these ever collide, something is very wrong.
    """
    if not _high_altitude_yaml().exists():
        pytest.skip("high-altitude-objects-2023 narratives not yet committed")

    nj = load_narrative_defs(_nj_drones_yaml())
    hab = load_narrative_defs(_high_altitude_yaml())
    nj_slugs = {d["slug"] for d in nj}
    hab_slugs = {d["slug"] for d in hab}
    assert nj_slugs != hab_slugs


# ---------------------------------------------------------------------------
# Resolver behavior
# ---------------------------------------------------------------------------


def test_find_narratives_yaml_default_topic_resolves() -> None:
    """The walk-up resolver must find data/nj-drones/narratives.yaml when
    called without arguments."""
    path = find_narratives_yaml()
    assert path.exists()
    assert path.name == "narratives.yaml"
    assert "nj-drones" in path.parts


def test_find_narratives_yaml_accepts_topic_slug() -> None:
    """Passing an explicit topic must resolve data/{topic}/narratives.yaml."""
    if not _high_altitude_yaml().exists():
        pytest.skip("high-altitude-objects-2023 narratives not yet committed")

    path = find_narratives_yaml(topic="high-altitude-objects-2023")
    assert path.exists()
    assert "high-altitude-objects-2023" in path.parts


def test_find_narratives_yaml_unknown_topic_raises() -> None:
    with pytest.raises(FileNotFoundError):
        find_narratives_yaml(topic="not-a-real-topic-xyz")


# ---------------------------------------------------------------------------
# Module default
# ---------------------------------------------------------------------------


def test_module_narrative_defs_populated_by_default() -> None:
    """NARRATIVE_DEFS is populated at import time from the nj-drones walk-up.
    This is the backward-compat contract the rest of the code depends on."""
    assert len(NARRATIVE_DEFS) > 0


# ---------------------------------------------------------------------------
# Malformed-YAML handling (loud failure contract)
# ---------------------------------------------------------------------------


def test_load_narrative_defs_empty_file_raises(tmp_path: Path) -> None:
    """An empty YAML file must raise ValueError with a clear message rather
    than AttributeError on the None returned by yaml.safe_load."""
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    with pytest.raises(ValueError, match="empty or contains only comments"):
        load_narrative_defs(empty)


def test_load_narrative_defs_comments_only_raises(tmp_path: Path) -> None:
    """A YAML file with only comments loads to None and must fail loudly."""
    comments = tmp_path / "comments.yaml"
    comments.write_text("# just a comment\n# nothing else\n")
    with pytest.raises(ValueError, match="empty or contains only comments"):
        load_narrative_defs(comments)


def test_load_narrative_defs_non_mapping_root_raises(tmp_path: Path) -> None:
    """A YAML file whose root is a list (not a mapping) must fail loudly."""
    bad_root = tmp_path / "bad-root.yaml"
    bad_root.write_text("- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="must be a mapping"):
        load_narrative_defs(bad_root)


def test_load_narrative_defs_non_list_narratives_raises(tmp_path: Path) -> None:
    """If 'narratives' is present but is not a list, fail loudly."""
    bad = tmp_path / "bad-narratives.yaml"
    bad.write_text("narratives:\n  slug: foo\n  keywords: [a, b]\n")
    with pytest.raises(ValueError, match="not a list"):
        load_narrative_defs(bad)


def test_load_narrative_defs_invalid_yaml_syntax_raises(tmp_path: Path) -> None:
    """Syntactically invalid YAML (unclosed sequence) must be caught and
    re-raised as ValueError so the CLI wrapper can exit cleanly."""
    bad = tmp_path / "invalid.yaml"
    bad.write_text("narratives:\n  - slug: [unclosed\n")
    with pytest.raises(ValueError, match="not valid YAML"):
        load_narrative_defs(bad)


def test_load_narrative_defs_non_dict_entry_raises(tmp_path: Path) -> None:
    """A narratives-list entry that is a bare string (not a mapping) must
    fail loudly rather than crashing later when the code dereferences keys."""
    bad = tmp_path / "bad-entry.yaml"
    bad.write_text("narratives:\n  - just-a-string\n")
    with pytest.raises(ValueError, match="entry 0 must be a mapping"):
        load_narrative_defs(bad)


def test_load_narrative_defs_entry_missing_slug_raises(tmp_path: Path) -> None:
    """A narratives-list entry that omits the required 'slug' key must fail
    loudly rather than raising KeyError later."""
    bad = tmp_path / "missing-slug.yaml"
    bad.write_text("narratives:\n  - hypothesis_id: H1\n    keywords: [foo]\n")
    with pytest.raises(ValueError, match="missing the required 'slug' key"):
        load_narrative_defs(bad)


def test_load_narrative_defs_string_keywords_raises(tmp_path: Path) -> None:
    """A string 'keywords' value (rather than a list) must fail loudly.
    Otherwise downstream list() would iterate it character-by-character and
    silently produce wrong narrative matches on unrelated documents."""
    bad = tmp_path / "string-keywords.yaml"
    bad.write_text("narratives:\n  - slug: n1\n    hypothesis_id: H1\n    keywords: balloon\n")
    with pytest.raises(ValueError, match="'keywords' value that is not a list"):
        load_narrative_defs(bad)


def test_load_narrative_defs_non_string_keyword_entry_raises(tmp_path: Path) -> None:
    """An individual keyword that is not a string (integer, list, mapping)
    must fail loudly."""
    bad = tmp_path / "bad-keyword.yaml"
    bad.write_text("narratives:\n  - slug: n1\n    hypothesis_id: H1\n    keywords: [foo, 42]\n")
    with pytest.raises(ValueError, match="keyword 1 must be a string"):
        load_narrative_defs(bad)


def test_load_narrative_defs_integer_hypothesis_id_coerced(tmp_path: Path) -> None:
    """An unquoted integer hypothesis_id must be coerced to a string
    rather than crashing on the '-' in int check. The coerced value
    is the integer's str form; the loader's job is not to reject
    unusual hypothesis ids, only to avoid a TypeError crash."""
    valid = tmp_path / "int-hypothesis.yaml"
    valid.write_text("narratives:\n  - slug: n1\n    hypothesis_id: 4\n    keywords: [foo]\n")
    defs = load_narrative_defs(valid)
    assert defs[0]["hypothesis"] == "4"
    assert all("slug" in d for d in NARRATIVE_DEFS)
