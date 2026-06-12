"""Cross-cutting constants for the signal methods package.

Single source of truth for thresholds, window sizes, source-kind partitions,
and narrative definitions. Other modules import from here rather than defining
their own copies. Narrative definitions are loaded from narratives.yaml at
import time so the YAML is authoritative and the code never diverges.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Hypothesis identifiers (CU26 H1-H5 framework)
# ---------------------------------------------------------------------------

H1, H2, H3, H4, H5 = "H1", "H2", "H3", "H4", "H5"

HYPOTHESIS_COUNT: int = 5
# Shannon entropy ceiling for a uniform distribution over HYPOTHESIS_COUNT
# hypotheses. The entropy-floor advisory and the resistance-ratio calculation
# normalize observed entropy against this value. Lifting this to a named
# constant makes the HYPOTHESIS_COUNT assumption explicit wherever it appears
# (Python eval and CLI today; TypeScript dashboard and schema pending a
# cross-language pass).
MAX_ENTROPY_BITS: float = math.log2(HYPOTHESIS_COUNT)


# ---------------------------------------------------------------------------
# Source-kind partitions for IVI
# ---------------------------------------------------------------------------

DISCOURSE_SOURCE_KINDS: frozenset[str] = frozenset({"news", "social", "forum", "podcast"})
AUTHORITATIVE_SOURCE_KINDS: frozenset[str] = frozenset({"gov", "academic", "aviation"})


# ---------------------------------------------------------------------------
# Rolling window defaults (method-specific, intentionally different)
# ---------------------------------------------------------------------------

IVI_DEFAULT_WINDOW_DAYS: int = 7  # IVI uses wider windows for stability
NVD_DEFAULT_WINDOW_DAYS: int = 3  # NVD uses tighter windows for responsiveness
EVAL_IVI_WINDOW_DAYS: int = 3  # Composite capture-risk uses 3-day IVI to
# match NVD temporal resolution (see sqm.md
# denser corpus validation section)


# ---------------------------------------------------------------------------
# Evidence and signal thresholds
# ---------------------------------------------------------------------------

EVIDENCE_THRESHOLD: float = 0.35  # min hypothesis score to count as evidence
LAPLACE_SMOOTHER: int = 1  # IVI and NVD denominator smoothing

# Composite narrative-capture risk thresholds.
# An alert fires when all three conditions converge on one narrative on one day.
# NVD threshold was lowered from 1.5 to 1.1 after the 204-doc corpus expansion:
# denser corpora compress NVD ratios because more evidence appears per window.
# An NVD of 1.2 with independence 1.0 (pure echo chamber) is still a meaningful
# divergence signal. The threshold should sit just above 1.0 (where narrative
# velocity equals evidence velocity, i.e. no divergence).
CAPTURE_RISK_IVI_THRESHOLD: float = 5.0  # IVI >= this (vacuum exists)
CAPTURE_RISK_NVD_THRESHOLD: float = 1.1  # NVD >= this (narrative outpacing evidence)
CAPTURE_RISK_INDEPENDENCE_THRESHOLD: float = 2.0  # independence <= this (echo chamber)


# ---------------------------------------------------------------------------
# Narrative definitions, loaded from narratives.yaml
# ---------------------------------------------------------------------------

DEFAULT_TOPIC: str = "nj-drones"


def find_narratives_yaml(topic: str = DEFAULT_TOPIC) -> Path:
    """Walk up from this file to find data/{topic}/narratives.yaml.

    The default topic is nj-drones, which is the validated baseline case.
    Pass a different topic slug to resolve a sibling corpus's narratives
    (e.g. "high-altitude-objects-2023"). Raises FileNotFoundError if the
    file is not reachable from this module's location upward.
    """
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        candidate = ancestor / "data" / topic / "narratives.yaml"
        if candidate.exists():
            return candidate
    msg = (
        f"Cannot find data/{topic}/narratives.yaml. "
        "Ensure the working directory is within the dev/tell/ subtree "
        f"and that the topic slug {topic!r} corresponds to a committed corpus."
    )
    raise FileNotFoundError(msg)


def load_narrative_defs(yaml_path: str | Path) -> list[dict[str, Any]]:
    """Load narrative definitions from YAML, normalizing to the code-level format.

    The YAML is the single source of truth. This function extracts the fields
    that the signal methods need: slug, hypothesis (code-level H1-H5 bucket),
    and keywords. The YAML may contain richer metadata (label, category,
    originating_source, etc.) that is preserved for display purposes.

    Accepts either str or pathlib.Path for the yaml_path argument. Raises
    FileNotFoundError if the file does not exist.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Narrative YAML not found at {path}")

    with open(path) as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Narrative YAML at {path} is not valid YAML: {exc}") from exc

    if raw is None:
        raise ValueError(
            f"Narrative YAML at {path} is empty or contains only comments. "
            "Expected a mapping with a 'narratives' key."
        )
    if not isinstance(raw, dict):
        raise ValueError(
            f"Narrative YAML at {path} must be a mapping with a 'narratives' key, "
            f"got {type(raw).__name__}."
        )

    narratives_raw = raw.get("narratives", [])
    if not isinstance(narratives_raw, list):
        raise ValueError(
            f"Narrative YAML at {path} has a 'narratives' key that is not a list "
            f"(got {type(narratives_raw).__name__}). Expected a list of narrative entries."
        )
    defs: list[dict[str, Any]] = []
    for idx, n in enumerate(narratives_raw):
        if not isinstance(n, dict):
            raise ValueError(
                f"Narrative YAML at {path} entry {idx} must be a mapping "
                f"(got {type(n).__name__}). Each entry needs a 'slug' and "
                "should include hypothesis_id and keywords."
            )
        if "slug" not in n:
            raise ValueError(
                f"Narrative YAML at {path} entry {idx} is missing the required 'slug' key."
            )

        # hypothesis_id may be absent, a plain H1-H5 string, or a richer
        # label like "H4-foreign". Coerce to string so a YAML author who
        # writes an unquoted integer does not trip the subsequent "-" check
        # with a TypeError that escapes the controlled-failure surface.
        raw_hyp = n.get("hypothesis_id") or n.get("hypothesis", "")
        hypothesis_id = str(raw_hyp) if raw_hyp is not None else ""
        if "-" in hypothesis_id:
            hypothesis_id = hypothesis_id.split("-")[0]

        # keywords must be a list of strings. A bare string (YAML author
        # writes "keywords: balloon" instead of "keywords: [balloon]")
        # would downstream be iterated character-by-character as match
        # tokens, producing plausible-looking but wrong narrative matches.
        # Fail loud here rather than silently corrupt scoring.
        raw_keywords = n.get("keywords", [])
        if not isinstance(raw_keywords, list):
            raise ValueError(
                f"Narrative YAML at {path} entry {idx} has a 'keywords' value "
                f"that is not a list (got {type(raw_keywords).__name__}). "
                "Use 'keywords: [foo, bar]' YAML list syntax."
            )
        for k_idx, kw in enumerate(raw_keywords):
            if not isinstance(kw, str):
                raise ValueError(
                    f"Narrative YAML at {path} entry {idx} keyword {k_idx} "
                    f"must be a string (got {type(kw).__name__})."
                )

        defs.append(
            {
                "slug": n["slug"],
                "hypothesis": hypothesis_id,
                "keywords": raw_keywords,
                "label": n.get("label", n["slug"]),
                "originating_source": n.get("originating_source", ""),
            }
        )
    return defs


# Load at import time. If the YAML is missing (e.g. running tests from a
# different directory), fall back to an empty list and let callers pass
# narrative_defs explicitly.
try:
    _NARRATIVES_YAML_PATH = find_narratives_yaml()
    NARRATIVE_DEFS: list[dict[str, Any]] = load_narrative_defs(_NARRATIVES_YAML_PATH)
except FileNotFoundError:
    NARRATIVE_DEFS = []


__all__ = [
    "AUTHORITATIVE_SOURCE_KINDS",
    "CAPTURE_RISK_INDEPENDENCE_THRESHOLD",
    "CAPTURE_RISK_IVI_THRESHOLD",
    "CAPTURE_RISK_NVD_THRESHOLD",
    "DEFAULT_TOPIC",
    "DISCOURSE_SOURCE_KINDS",
    "EVAL_IVI_WINDOW_DAYS",
    "EVIDENCE_THRESHOLD",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "IVI_DEFAULT_WINDOW_DAYS",
    "LAPLACE_SMOOTHER",
    "NARRATIVE_DEFS",
    "NVD_DEFAULT_WINDOW_DAYS",
    "find_narratives_yaml",
    "load_narrative_defs",
]
