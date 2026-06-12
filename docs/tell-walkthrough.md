# TELL Pipeline Walkthrough

An end-to-end explanation of the TELL weak-signal detection pipeline: the research problem, hypothesis, three novel methods, hypothesis scoring system, sensemaking quality metrics, engineering architecture, and validation results. Written at "explain like I'm five" depth where the concepts benefit from it.

## The Research Problem

When something weird happens and the government doesn't explain it quickly, people fill the silence with stories. Some of those stories are true, some are false, and some are a mix. The problem is: **how do you tell the difference in real time, before anyone knows the answer?**

The NJ drones incident in late 2024 is the case study. Thousands of people saw things in the sky over New Jersey. The FBI, FAA, DHS, and DoD all said "nothing anomalous" but didn't explain what the things actually were. That silence (the "information vacuum") lasted 38 days. During those 38 days:

- A congressman claimed Iran had a drone mothership off the coast (it didn't)
- A podcast host speculated about a loose nuclear weapon (there wasn't one)
- The government's default framing was "mass hysteria" (some sightings were real)

Each of these narratives shaped real behavior: citizens shot at the sky, laser strikes against commercial aircraft surged 269%.

**The core insight:** Existing OSINT tools try to *predict what happened*. TELL asks a different question: **is the sensemaking process itself working?** Are institutions responding to public discourse? Are narratives supported by evidence? Is apparent corroboration real, or just one claim echoed six times?

## The Hypothesis

You can build computational metrics that detect when sensemaking is failing, using three signals:

1. **Is there a vacuum?** (Are people talking but institutions silent?)
2. **Are narratives outpacing evidence?** (Is a claim spreading faster than facts can support it?)
3. **Is corroboration real?** (Do six articles represent six independent observations, or one claim repeated?)

These are grounded in two academic frameworks:
- **Klein (2007)** on six cognitive activities that characterize expert sensemaking (Elaborating, Questioning, Connecting, Comparing, Framing, Re-Framing)
- **Leveson (2012)** on STAMP, which models accidents as control-loop failures. TELL treats the information environment as a control system: institutions are the controller, public discourse is the controlled process, and IVI measures whether the feedback loop is working.

## The Three Novel Methods

### IVI: Information Vacuum Index

**ELI5:** Count how many news articles are talking about drones, count how many government statements are responding, divide them.

```
IVI = discourse_documents / (authoritative_documents + 1)
```

- "Discourse" = news, social media, podcasts, forums
- "Authoritative" = government (.gov), academic, aviation authority
- The `+1` prevents dividing by zero and keeps the numbers human-readable

**What it found:** IVI peaked at **17.0** on Dec 24, 2024: 17 news articles in a 7-day window, zero government responses. The vacuum was deepest *after* the FAA issued flight restrictions and then went silent, not when the first sightings hit the news.

### NVD: Narrative Velocity Divergence

**ELI5:** For a specific claim (like "Iranian Mothership"), count how fast the *story* is spreading vs. how fast the *evidence for it* is growing. If the story is spreading way faster than evidence supports it, that's a red flag.

```
NVD = narrative_velocity / (evidence_velocity + 1)
```

- "Narrative velocity" = how many documents mention this narrative in the rolling window
- "Evidence velocity" = how many of those documents actually score above 0.35 on the narrative's hypothesis
- NVD > 1.0 means the narrative is outrunning its evidence

**What it found:** The Iranian Mothership narrative hit NVD **1.20** on Dec 11 (higher in smaller corpora: 2.00 at 38 docs). The story spread faster than its evidence. Meanwhile, "legitimate drones" had NVD **1.53** on Dec 18, but with much higher independence (real diverse reporting, not echo).

### SIG: Source Independence Graph

**ELI5:** If six newspapers say the same thing, that *looks* like six independent confirmations. But if all six are just repeating what one congressman said on Fox News, it's actually one source echoed six times. SIG figures out which is which.

**How it works:**
1. Find all documents mentioning a narrative
2. Look at titles for attribution signals ("Van Drew says...", "according to...")
3. Classify each source domain as: **origin** (started the claim), **independent** (reported it without attributing to another source), or **amplifier** (reported it by citing someone else)
4. Compute: `independence_score = independent_sources + 1`, `amplification_ratio = total_docs / independence_score`

**What it found:** Iranian Mothership: **independence score 1, amplification 6x**. One origin (Van Drew), zero independent sources, six outlets echoing. This is invariant across all three corpus sizes (38, 96, 204 docs). It is the structural signature of an echo chamber.

## The Hypothesis Scoring System (H1-H5)

Every document gets scored against five competing hypotheses using batched LLM calls (Claude Haiku):

| Hypothesis | What it means |
|---|---|
| H1 | Sensor artifact / misidentification |
| H2 | Natural phenomenon |
| H3 | Human-made, unclassified (drones, test flights) |
| H4 | Human-made, classified (military, foreign) |
| H5 | Unknown / genuinely anomalous |

Scores are **independent probabilities** [0, 1], not forced-choice. A single document can score 0.7 on H3 and 0.4 on H4 simultaneously. This preserves ambiguity rather than forcing premature classification.

Daily distributions track how the evidence landscape evolves over time. The system is most uncertain (highest entropy) on Dec 11, the day of maximum narrative chaos. It never collapses to a single hypothesis, even at the Jan 28 resolution event.

## Sensemaking Quality Metrics (SQM)

Four metrics that evaluate whether the pipeline is doing its job:

1. **Contradicting evidence lag.** How quickly does the pipeline surface evidence that challenges a dominant narrative? Iranian Mothership: **0 hours** (Pentagon denial enters the same day). Mass Hysteria: **1,128 hours** (47 days unchallenged, a genuine finding about the information environment).

2. **Composite narrative-capture risk.** All three signals (high IVI + high NVD + low independence) converging on one narrative on one day. **Dec 11 and Dec 12 both fire.** That convergence is the structural precondition for narrative capture.

3. **Evidence-narrative alignment.** Are the loudest narratives also the best-supported? **95.7% of windows** show alignment. The 4.3% misalignment is where the interesting failures live.

4. **Premature closure resistance.** Does the system maintain appropriate uncertainty? **Mean entropy 86.5%** of theoretical maximum across 26 days. The system never collapses to one hypothesis.

## The Engineering Architecture

```
Seeds (YAML)  →  Python Ingestion  →  Vercel Blob (raw HTML)
                                    →  Neon Postgres (metadata)
                                          ↓
                   Python Scoring (H1-H5 via Claude Haiku)
                                          ↓
                   Python Signals (IVI, NVD, SIG)
                                          ↓
                   Python Evaluation (SQM metrics)
                                          ↓
                   Neon Postgres (signal tables)
                                          ↓
                   Next.js 16 Dashboard (Server Components)
                      ├─ Corpus summary
                      ├─ Sensemaking Activities grid (Klein/Leveson)
                      ├─ IVI chart (hand-drawn SVG)
                      ├─ Hypothesis distribution chart
                      ├─ NVD divergence chart
                      ├─ Independence table + React Flow graph
                      └─ Document list
```

**Key design decisions:**

- **Python runs offline** (laptop + CI). No Python on Vercel for the demo. The dashboard reads precomputed results.
- **No database dependency in signal methods.** IVI, NVD, and SIG accept plain Python iterables. They can be unit-tested against fixtures without touching Neon.
- **Keyword matching over ML clustering.** At 204 documents, expert-curated keyword patterns are more defensible than learned topic models. Honest about the scale limitation.
- **Corpus versioning via Neon branches.** The demo will be pinned to a frozen branch so nothing changes under the presenter.
- **Unique constraints everywhere.** Re-running any pipeline stage is idempotent. Signal rows upsert on natural keys.

## The Validation Story

The pipeline has been validated across three corpus densities:

| Metric | 38 docs | 96 docs | 204 docs |
|---|---|---|---|
| IVI peak (7-day) | 15.00 | 11.33 | 17.00 |
| Iranian Mothership NVD | 2.00 | 1.50 | 1.20 |
| Iranian Mothership SIG score | 1 | 1 | 1 |
| Contradicting evidence lag (IM) | 0 hours | 0 hours | 0 hours |
| Composite alerts | Dec 11, 13 | Dec 11 | Dec 11, 12 |

Echo-chamber signals (SIG) are **completely invariant** across corpus sizes. NVD ratios compress as expected (more evidence per window). IVI varies with corpus composition but always identifies the same vacuum window. The stability across three builds is itself a methodological contribution.

**Six of eight abstract claims are validated. Two are partial (contradicting evidence for mass-hysteria, Klein/Leveson interactive interface). Zero are unproven.**

## Why It Matters

This is not an AI prediction tool. It does not tell you what the drones are. It tells you whether the *process of figuring out what the drones are* is working. That distinction matters for:

- **Biosecurity:** ambiguous early reports, slow institutional response
- **Emerging tech governance:** public discourse outpaces regulatory understanding
- **Critical infrastructure:** competing explanations before root cause analysis
- **Algorithmic amplification:** platforms accelerate narratives independent of evidence

The policy question in each case is the same: how should institutions manage information environments when they cannot yet provide an authoritative answer?
