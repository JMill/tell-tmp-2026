"""Source Independence Graph (SIG).

The Source Independence Graph answers: for a given narrative, how many truly
independent sources support it, versus how many outlets are simply echoing
a single originating claim?

Corroboration vs. echo amplification
--------------------------------------
A claim is *corroborated* if it is independently asserted by multiple sources
that are not tracing back to a single originating statement. A claim is *echo
amplified* if many outlets repeat it while all citing (directly or indirectly)
a single origin.

Example: Van Drew's Iranian Mothership claim. 20+ outlets reported it.
But they all cited "a statement by Rep. Van Drew" or Fox News (which first
aired the statement). The independence score for this narrative is ~1
(one independent root: Van Drew's press statement). The echo amplification
ratio is ~20.

Algorithm
---------
For each narrative N:

  1. Classify which documents match N (same keyword matching as NVD).
  2. Extract the unique source domains from those documents.
  3. Check attribution signals: does the document title suggest it is
     REPORTING ON another source's claim (attribution patterns like
     "X says", "X claims", "according to X") vs. making an independent claim?
  4. Classify each source as:
       - "origin": the narrative's originating source (from narratives.yaml)
       - "independent": a domain asserting the claim without attribution to
         another corpus source
       - "amplifier": a domain reporting that another corpus source made the claim
  5. Compute:
       independence_score = count(independent sources) + 1  (the origin)
       amplification_ratio = count(amplifiers) / independence_score

A narrative with independence_score == 1 and a high amplification_ratio
is a canonical echo chamber: many outlets, one root.

Attribution heuristics
----------------------
The text available without re-fetching blobs is the document title and URL.
The following title patterns indicate attribution (document is repeating
someone else's claim):
  - "X says ...", "X claims ...", "X: ..."
  - "according to X", "per X", "report: X"
  - "Van Drew says", "Pentagon says", "White House says"

Known originating entities per narrative are extracted from the narrative's
`originating_source` field in narratives.yaml and supplemented with a
known-entities list below.

No blob I/O. All computation is done over document titles and URLs already
in Neon, which keeps the SIG computation cheap and repeatable without
requiring access to the raw HTML store.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from signals_methods.constants import NARRATIVE_DEFS
from signals_methods.nvd import NvdDocument, _matches_narrative

# Attribution signal patterns (case-insensitive).
# If a document title matches any of these patterns it is classified as
# an amplifier (reporting on someone else's claim) rather than an
# independent source.
_ATTRIBUTION_PATTERNS = [
    r"\bsays?\b",
    r"\bclaims?\b",
    r"\breports?\b",
    r"\baccording to\b",
    r"\bper\b.{0,20}\b(say|claim|report|state|assert)\b",
    r":\s+[A-Z]",  # "Van Drew: Iranian ship..."  headline colon format
]

_ATTRIBUTION_RE = re.compile("|".join(_ATTRIBUTION_PATTERNS), re.IGNORECASE)

# Known entities whose names in a title indicate attribution.
# Matched case-insensitively as substrings.
_KNOWN_ATTRIBUTORS = [
    "van drew",
    "pentagon",
    "white house",
    "biden",
    "trump",
    "faa",
    "dhs",
    "fbi",
    "dod",
    "norad",
    "hogan",
    "singh",
    "leavitt",
    "aaro",
    "fema",
    "nnsa",
    "doe",
]

# Map from narrative slug → originating entity label (for display)
_NARRATIVE_ORIGINS: dict[str, str] = {
    "iranian-mothership": "Rep. Jeff Van Drew (R-NJ)",
    "loose-nuke": "Podcast (unspecified)",
    "test-flights": "Online forums / Trump White House",
    "war-game": "Online forums",
    "false-flag": "Project Blue Beam / Online forums",
    "mass-hysteria": "Biden White House / Mainstream media",
    "uap": "Online and mainstream media",
    "drones-legit": "Initial military reports",
}


@dataclass
class SourceNode:
    """One source domain in the independence graph."""

    domain: str
    document_count: int
    role: str  # "origin" | "independent" | "amplifier"
    titles: list[str] = field(default_factory=list)


@dataclass
class IndependenceResult:
    """SIG result for one narrative."""

    narrative_slug: str
    narrative_label: str
    origin_label: str
    total_documents: int
    unique_domains: int
    independent_sources: int  # domains making non-attributed claims
    amplifier_sources: int  # domains reporting on another source's claim
    independence_score: float  # independent_sources + 1 (the origin)
    amplification_ratio: float  # total_documents / independence_score
    sources: list[SourceNode] = field(default_factory=list)


_SUBDOMAIN_PREFIXES = ("www.", "amp.", "m.", "mobile.", "edition.", "feeds.", "rss.")


def _extract_domain(url: str) -> str:
    """Return the registrable domain, stripping common subdomain prefixes.

    Handles www., amp., m., mobile., edition., feeds., and rss. prefixes
    that represent the same outlet. For full eTLD+1 normalization (e.g.
    co.uk, com.au), add the tldextract library as a future enhancement.
    """
    try:
        host = urlparse(url).netloc.lower()
        for prefix in _SUBDOMAIN_PREFIXES:
            if host.startswith(prefix):
                host = host[len(prefix) :]
        return host
    except Exception:
        return url


def _is_amplifier(title: str) -> bool:
    """Return True if the title suggests the document is attributing a claim."""
    if _ATTRIBUTION_RE.search(title):
        return True
    lower = title.lower()
    return any(entity in lower for entity in _KNOWN_ATTRIBUTORS)


def compute_independence(
    documents: list[NvdDocument],
    *,
    narrative_defs: list[dict[str, object]] | None = None,
) -> list[IndependenceResult]:
    """Compute the Source Independence Graph for all narratives.

    Parameters
    ----------
    documents:
        All corpus documents. Must have title and url populated.
    narrative_defs:
        Narrative definitions. Defaults to NARRATIVE_DEFS. Override in tests.

    Returns
    -------
    list[IndependenceResult]
        One result per narrative, sorted by independence_score ascending
        (most echo-amplified first, matching the talk's expected finding).
    """
    ndefs = narrative_defs if narrative_defs is not None else NARRATIVE_DEFS

    results: list[IndependenceResult] = []

    for ndef in ndefs:
        slug = str(ndef["slug"])
        keywords = list(ndef["keywords"])  # type: ignore[arg-type]

        # Prefer the narrative-def's own label and originating_source (loaded
        # from narratives.yaml via load_narrative_defs). Fall back to the
        # NJ-drones hardcoded map only when the loaded def omits the field,
        # so that non-default corpora (e.g. --narratives high-altitude-objects)
        # surface their authoritative labels and origins instead of slug
        # fallbacks and "Unknown".
        label_raw = ndef.get("label") if isinstance(ndef, dict) else None
        label = str(label_raw) if label_raw else slug
        origin_raw = ndef.get("originating_source") if isinstance(ndef, dict) else None
        origin = str(origin_raw) if origin_raw else _NARRATIVE_ORIGINS.get(slug, "Unknown")

        matched = [doc for doc in documents if _matches_narrative(doc, keywords)]
        if not matched:
            results.append(
                IndependenceResult(
                    narrative_slug=slug,
                    narrative_label=label,
                    origin_label=origin,
                    total_documents=0,
                    unique_domains=0,
                    independent_sources=0,
                    amplifier_sources=0,
                    independence_score=1.0,
                    amplification_ratio=0.0,
                )
            )
            continue

        # Group documents by domain
        by_domain: dict[str, SourceNode] = {}
        for doc in matched:
            domain = _extract_domain(doc.url)
            if domain not in by_domain:
                by_domain[domain] = SourceNode(
                    domain=domain,
                    document_count=0,
                    role="independent",
                )
            node = by_domain[domain]
            node.document_count += 1
            node.titles.append(doc.title)

        # Classify each domain
        for node in by_domain.values():
            # If the majority of this domain's titles show attribution signals,
            # classify as amplifier
            amplifier_votes = sum(1 for t in node.titles if _is_amplifier(t))
            if amplifier_votes > len(node.titles) * 0.5:
                node.role = "amplifier"

        independent_sources = sum(1 for n in by_domain.values() if n.role == "independent")
        amplifier_sources = sum(1 for n in by_domain.values() if n.role == "amplifier")
        independence_score = float(independent_sources + 1)  # +1 for origin
        amplification_ratio = len(matched) / independence_score if independence_score > 0 else 0.0

        results.append(
            IndependenceResult(
                narrative_slug=slug,
                narrative_label=label,
                origin_label=origin,
                total_documents=len(matched),
                unique_domains=len(by_domain),
                independent_sources=independent_sources,
                amplifier_sources=amplifier_sources,
                independence_score=independence_score,
                amplification_ratio=amplification_ratio,
                sources=sorted(by_domain.values(), key=lambda n: n.document_count, reverse=True),
            )
        )

    return sorted(results, key=lambda r: r.independence_score)
