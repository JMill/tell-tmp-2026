"""Unit tests for the batch loader and SeedEntry parsing.

Does not exercise live network calls — those live in the smoke test.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from signals_ingest.batch import SeedEntry, load_seed_file


def test_seed_entry_from_dict_full() -> None:
    entry = SeedEntry.from_dict(
        {
            "url": "https://example.com/article",
            "source_kind": "gov",
            "adapter": "direct",
            "event_date": "2024-12-11",
            "narratives": ["iranian-mothership"],
            "notes": "Some context",
        }
    )
    assert entry.url == "https://example.com/article"
    assert entry.source_kind == "gov"
    assert entry.adapter == "direct"
    assert entry.event_date == "2024-12-11"
    assert entry.narratives == ["iranian-mothership"]
    assert entry.notes == "Some context"


def test_seed_entry_from_dict_minimal() -> None:
    """Only url is required; the rest default sensibly."""
    entry = SeedEntry.from_dict({"url": "https://example.com/article"})
    assert entry.url == "https://example.com/article"
    assert entry.source_kind == "news"  # default
    assert entry.adapter == "wayback"  # default
    assert entry.event_date is None
    assert entry.narratives == []
    assert entry.notes is None


def test_load_seed_file(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent(
        """\
        metadata:
          corpus: test-corpus
          total_entries: 2

        seeds:
          - url: https://example.com/a
            source_kind: gov
            adapter: direct
            event_date: 2024-12-11
            narratives: [iranian-mothership]

          - url: https://example.com/b
            source_kind: news
            adapter: wayback
        """
    )
    seeds_path = tmp_path / "seed-urls.yaml"
    seeds_path.write_text(yaml_content)

    seeds = load_seed_file(seeds_path)
    assert len(seeds) == 2
    assert seeds[0].url == "https://example.com/a"
    assert seeds[0].adapter == "direct"
    assert seeds[0].narratives == ["iranian-mothership"]
    assert seeds[1].url == "https://example.com/b"
    assert seeds[1].adapter == "wayback"


def test_load_seed_file_rejects_missing_seeds_key(tmp_path: Path) -> None:
    yaml_content = "metadata:\n  corpus: test\n"
    seeds_path = tmp_path / "bad.yaml"
    seeds_path.write_text(yaml_content)
    with pytest.raises(ValueError, match="top-level 'seeds' key"):
        load_seed_file(seeds_path)


def test_load_seed_file_rejects_non_list_seeds(tmp_path: Path) -> None:
    yaml_content = "seeds:\n  url: not-a-list\n"
    seeds_path = tmp_path / "bad.yaml"
    seeds_path.write_text(yaml_content)
    with pytest.raises(ValueError, match="'seeds' must be a list"):
        load_seed_file(seeds_path)


def test_load_real_seed_file() -> None:
    """Smoke check: the real NJ drones seed file parses cleanly and has the
    expected shape."""
    here = Path(__file__).resolve()
    # Walk up to dev/tell/ and then down to data/nj-drones/seed-urls.yaml
    repo_seed = None
    for parent in here.parents:
        candidate = parent / "data" / "nj-drones" / "seed-urls.yaml"
        if candidate.exists():
            repo_seed = candidate
            break
    assert repo_seed is not None, "Could not find data/nj-drones/seed-urls.yaml from test location"
    seeds = load_seed_file(repo_seed)
    assert len(seeds) >= 30, f"Expected at least 30 seeds in the real file, got {len(seeds)}"
    # Every entry has required fields
    for s in seeds:
        assert s.url.startswith("http")
        assert s.adapter in {"wayback", "direct"}
        assert s.source_kind in {
            "gov",
            "news",
            "social",
            "academic",
            "aviation",
            "forum",
            "podcast",
            "other",
        }
