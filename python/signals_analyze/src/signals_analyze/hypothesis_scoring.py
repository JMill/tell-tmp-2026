"""H1-H5 hypothesis scoring via Anthropic Claude with tool-call structured output.

For each document in a corpus, ask Claude to estimate the probability that the
document supports each of the five CU26 hypotheses, plus a brief rationale.

The five hypotheses (per data/hypotheses.yaml):
- H1 Data/Sensor Artifact
- H2 Natural Physical Source
- H3 Human-Made Physical Source (unclassified)
- H4 Human-Made Physical Source (classified)
- H5 Other (Unknown) Physical Phenomenon

## Prompt design

The prompt frames the task as evidence assessment, not classification. The
model is told that an article can support multiple hypotheses simultaneously
(probabilities do not need to sum to 1) and that "support" means "the article
contains evidence consistent with this hypothesis being the explanation," NOT
"the article asserts this hypothesis is correct." A news article reporting
that the Pentagon denied an Iranian mothership claim supports H4 (it documents
that the question of foreign tech is being addressed) AND simultaneously
weakens the iranian-mothership narrative claim.

This avoids the trap of mistaking "this article quotes a partisan claim" for
"this article is evidence for that claim."

## Tool-use structured output

The model is given a `record_hypothesis_scores` tool with H1-H5 score fields
plus rationale. We force tool use via `tool_choice={"type": "tool", "name":
"record_hypothesis_scores"}` so the model cannot return free-form text. This
eliminates JSON parsing errors and prompt-injection risk in the output path.

## Idempotency

Each scoring call produces five rows in `document_hypothesis_scores` keyed on
(document_id, hypothesis_id, prompt_version, model). Re-running with the same
prompt version and model overwrites in place via ON CONFLICT.

## Cost

Per document with Haiku 4.5 and a typical NJ drones article (~3000 words text
truncated to 8000 chars):
- Input: ~3000 tokens (system prompt + document content)
- Output: ~300 tokens (tool call with 5 scores + rationale)
- Cost: ~$0.0007 per document

For the 38-document corpus, total cost is well under $0.10.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from anthropic import Anthropic

# Bumping this version creates a new row in document_hypothesis_scores rather
# than overwriting prior scores. Use semver-like increments: -v1, -v1.1, -v2.
HYPOTHESIS_PROMPT_VERSION = "h15-v1"

# Default model. Haiku 4.5 is fast and cheap; quality has been adequate for
# this task in spot checks. Promote to Sonnet for higher-stakes runs.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Maximum characters of document text to send to the model. Trafilatura
# extracts can be many thousands of words; we truncate to keep input cost
# bounded and stay well under the model's context window.
MAX_DOCUMENT_CHARS = 8000

HypothesisId = Literal["H1", "H2", "H3", "H4", "H5"]


@dataclass(frozen=True)
class HypothesisScores:
    """One scoring result: a probability for each H1-H5 plus a rationale.

    Probabilities are NOT constrained to sum to 1. Each is the model's
    independent estimate of whether this document supports that hypothesis.
    """

    h1: float
    h2: float
    h3: float
    h4: float
    h5: float
    rationale: str
    raw_input_tokens: int = 0
    raw_output_tokens: int = 0

    def as_dict(self) -> dict[HypothesisId, float]:
        return {"H1": self.h1, "H2": self.h2, "H3": self.h3, "H4": self.h4, "H5": self.h5}


SYSTEM_PROMPT = """You are an evidence-assessment assistant for a research pipeline studying information environments around ambiguous, high-uncertainty events. Your job is to read a single news article (or government statement, podcast description, etc.) and estimate, for each of five hypotheses, the probability that this specific document provides EVIDENCE supporting that hypothesis.

The hypotheses are:

- **H1 — Data/Sensor Artifact.** The observed phenomenon was a measurement or perception error: parallax, optical illusion, sensor calibration drift, multipath, ducting, atmospheric artifact, witness misidentification of a known stimulus.

- **H2 — Natural Physical Source.** A real natural phenomenon: birds, balloons, plasma, atmospheric phenomena, animals, geophysical events, or other naturally-occurring causes.

- **H3 — Human-Made Physical Source (unclassified).** Real but ordinary human technology: hobbyist drones, commercial aircraft, helicopters, satellites, the ISS, weather balloons. Things anyone can buy or operate without classification.

- **H4 — Human-Made Physical Source (classified).** Real human technology that is classified or restricted: U.S. military or intelligence developmental programs, foreign adversary systems (Russian, Chinese, Iranian, etc.), defense-contractor test flights, government or sub-contractor classified missions.

- **H5 — Other (Unknown) Physical Phenomenon.** Something that does not fit H1-H4: a genuinely unexplained physical phenomenon, non-human intelligence (NHI), unknown physics, or a residual unknown that the available evidence cannot resolve.

## What "evidence supporting" means

A score of 1.0 for H4 means: "This document contains substantial first-hand or institutional evidence that the answer is classified human technology — for example, a leaked DoD memo describing a specific program."

A score of 0.5 for H4 means: "This document raises the H4 hypothesis as plausible and provides moderate evidence for it — for example, an article quoting a senator who claims classified programs are involved AND providing corroborating context."

A score of 0.1 for H4 means: "This document mentions H4 in passing or quotes one unsupported assertion."

A score of 0.0 for H4 means: "This document has no bearing on H4 either way."

## Critical distinction

A document that REPORTS a partisan claim does not necessarily SUPPORT that claim. A news article whose headline is "Senator says Iranian mothership launching drones, Pentagon denies" provides:
- weak-to-moderate support for H4 (it documents that the question of foreign-adversary tech is being publicly raised),
- AND substantial counter-evidence to the specific Iranian mothership narrative (the Pentagon denial is on the record).

Score what the document EVIDENCES, not what its sources CLAIM. A debunking article SUPPORTS the hypothesis being debunked if and only if the debunking is incomplete or contested.

## Output

Probabilities are independent. They do NOT need to sum to 1 — a strong news report can support H1 (mass-misidentification framing) and H4 (classified-tech framing) simultaneously if both framings are documented in the article.

Provide a brief one-to-three sentence rationale that names the specific evidence in the document that drove your scores.

You MUST respond by invoking the record_hypothesis_scores tool. Do not produce free text."""


HYPOTHESIS_TOOL = {
    "name": "record_hypothesis_scores",
    "description": (
        "Record the H1-H5 hypothesis support scores for the current document. "
        "All five fields are required. Probabilities are independent and may not sum to 1."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "h1": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Probability the document supports H1 — Data/Sensor Artifact",
            },
            "h2": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Probability the document supports H2 — Natural Physical Source",
            },
            "h3": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Probability the document supports H3 — Human-Made (unclassified)",
            },
            "h4": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Probability the document supports H4 — Human-Made (classified)",
            },
            "h5": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Probability the document supports H5 — Other Unknown Phenomenon",
            },
            "rationale": {
                "type": "string",
                "description": (
                    "One-to-three sentences naming the specific evidence in the document "
                    "that drove the scores."
                ),
            },
        },
        "required": ["h1", "h2", "h3", "h4", "h5", "rationale"],
    },
}


def _get_client() -> Anthropic:
    """Construct an Anthropic client from the environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to the Vercel project env "
            "(`vercel env add ANTHROPIC_API_KEY`), pull with `vercel env pull "
            ".env.local --yes`, and re-run."
        )
    return Anthropic(api_key=api_key)


def score_document(
    *,
    title: str | None,
    text: str,
    url: str,
    source_kind: str,
    model: str = DEFAULT_MODEL,
    client: Anthropic | None = None,
    max_tokens: int = 1024,
) -> HypothesisScores:
    """Score a single document against H1-H5 via Anthropic tool use.

    Args:
        title: document title (optional but improves grounding)
        text: extracted document body text. Truncated to MAX_DOCUMENT_CHARS.
        url: canonical URL for context
        source_kind: source classification (news, gov, etc.) for context
        model: Anthropic model id, default Haiku 4.5
        client: optional Anthropic client (testing). If None, constructed from env.
        max_tokens: max output tokens for the response

    Returns:
        HypothesisScores with five probabilities, a rationale string, and raw
        token counts for cost tracking.

    Raises:
        RuntimeError if the model returned a non-tool response or if the tool
            arguments did not include all five hypothesis fields.
    """
    if client is None:
        client = _get_client()

    truncated = text[:MAX_DOCUMENT_CHARS]
    truncation_note = ""
    if len(text) > MAX_DOCUMENT_CHARS:
        truncation_note = (
            f"\n\n[Document truncated to {MAX_DOCUMENT_CHARS} characters. "
            f"Original length: {len(text)} characters.]"
        )

    user_message = (
        f"## Document metadata\n"
        f"- URL: {url}\n"
        f"- Source kind: {source_kind}\n"
        f"- Title: {title or '(no title)'}\n"
        f"\n## Document body\n\n{truncated}{truncation_note}\n\n"
        f"## Task\n\n"
        f"Score this document against H1-H5. Use the record_hypothesis_scores tool."
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=[HYPOTHESIS_TOOL],
        tool_choice={"type": "tool", "name": "record_hypothesis_scores"},
        messages=[{"role": "user", "content": user_message}],
    )

    # Find the tool_use block. With forced tool_choice the response should
    # have exactly one tool_use block.
    tool_block = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            tool_block = block
            break

    if tool_block is None:
        raise RuntimeError(
            f"Model {model} did not produce a tool_use block. Response content: "
            f"{response.content!r}"
        )

    args = tool_block.input
    if not isinstance(args, dict):
        raise RuntimeError(f"Tool arguments are not a dict: {args!r}")

    required = {"h1", "h2", "h3", "h4", "h5", "rationale"}
    missing = required - set(args.keys())
    if missing:
        raise RuntimeError(f"Tool arguments missing required fields: {missing}")

    # Coerce numbers and clamp to [0, 1] just in case the model exceeds the
    # schema bound (Anthropic enforces this server-side but defense in depth).
    def _clamp(v: object) -> float:
        f = float(v)  # type: ignore[arg-type]
        if f < 0.0:
            return 0.0
        if f > 1.0:
            return 1.0
        return f

    return HypothesisScores(
        h1=_clamp(args["h1"]),
        h2=_clamp(args["h2"]),
        h3=_clamp(args["h3"]),
        h4=_clamp(args["h4"]),
        h5=_clamp(args["h5"]),
        rationale=str(args["rationale"]),
        raw_input_tokens=response.usage.input_tokens,
        raw_output_tokens=response.usage.output_tokens,
    )
