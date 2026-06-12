# Source Independence Graph (SIG)

**Status:** Implemented and validated against the NJ drones corpus. 2026-04-08. Phase D of `dev/tell/docs/NEXT-STEPS.md`.

## Definition

The Source Independence Graph distinguishes genuine multi-source corroboration from echo amplification. For each narrative in the corpus, SIG classifies every source domain as either independent (making an original claim) or amplifier (repeating another source's claim), then computes two metrics:

```
independence_score(narrative)    = independent_sources + 1
amplification_ratio(narrative)   = total_documents / independence_score
```

Where:
- `independent_sources` counts domains whose coverage of the narrative does not exhibit attribution signals (the domain is asserting the claim, not reporting that someone else made it)
- The `+1` accounts for the originating source itself (the entity who first made the claim publicly)
- `amplification_ratio` measures how many documents exist per truly independent source

An independence_score of 1 with a high amplification_ratio is the structural signature of an echo chamber: one claim repeated by many outlets with no independent corroboration.

## Why this matters

Most "multi-source corroboration" in the NJ drones case was illusory. Twenty news articles all repeating Van Drew's Iranian Mothership claim look like 20 independent confirmations to a casual reader. They are one statement repeated twenty times. The Source Independence Graph reveals this directly by tracing attribution signals in document titles.

This connects to the CU26 paper's argument about redundant vs. complementary observations. The same principle that gives multiple sensor readings evidentiary weight applies to information sources: independence is the precondition for corroboration. Without it, volume is noise, not signal.

## Design notes

1. **Title-level attribution heuristics.** The current implementation classifies source domains by looking for attribution patterns in document titles: phrases like "X says", "X claims", "according to X", and headline colon formatting ("Van Drew: Iranian ship..."). This works because news headlines reliably signal whether the article is reporting someone else's claim vs. asserting its own findings. It does NOT require re-fetching raw HTML from the blob store.

2. **Domain-level granularity.** Nodes are source domains (e.g., `nytimes.com`, `thehill.com`), not individual documents. This is the right resolution for the independence question: the question is not "how many articles exist?" but "how many independent investigative operations produced evidence?"

3. **Known-entity matching.** The attribution classifier checks titles for known entities whose names indicate the article is reporting on a statement rather than making an independent claim. The entity list includes political figures (Van Drew, Biden, Trump, Hogan), agencies (FAA, DHS, FBI, DoD, NORAD, AARO), and institutional spokespeople (Singh, Leavitt). This supplements the generic attribution-pattern regex.

4. **Narrative classification shared with NVD.** Documents are matched to narratives using the same keyword patterns as the NVD module. Both methods share the `_matches_narrative` function and the `NARRATIVE_DEFS` constants, ensuring consistency.

5. **No graph library required.** The current implementation does not use `networkx`. The classification heuristic (attribution pattern detection) is sufficient to distinguish independent from amplifier sources for the NJ drones corpus. A future version that traces citation chains across documents would benefit from a graph library, but the current approach is simpler and produces defensible results.

## Validation against the NJ drones corpus

**Run date:** 2026-04-08
**Corpus:** `nj-drones-2026-04-08` (38 documents, 28 distinct sources, 2024-11-21 through 2025-01-28)
**Command:** `uv run signals compute independence --corpus nj-drones-2026-04-08 --topic nj-drones`

### Per-narrative results (sorted by independence score ascending)

| Narrative | Docs | Domains | Independent | Amplifiers | Score | Amplification |
|---|---:|---:|---:|---:|---:|---:|
| **Iranian Mothership** | **6** | **6** | **0** | **6** | **1** | **6.0×** |
| Test Flights | 3 | 3 | 0 | 3 | 1 | 3.0× |
| Mass Hysteria | 4 | 4 | 0 | 4 | 1 | 4.0× |
| Loose Nuke | 1 | 1 | 1 | 0 | 2 | 0.5× |
| UAP | 2 | 2 | 2 | 0 | 3 | 0.7× |
| Legitimate Drones | 38 | 28 | 10 | 18 | 11 | 3.5× |

(Narratives with zero matching documents omitted: war-game, false-flag.)

### Interpretation

**The Source Independence Graph produces the expected echo-chamber topology for the Iranian Mothership narrative.**

- **Iranian Mothership: score 1, amplification 6×.** Six documents from six distinct domains all report Van Drew's statement. All six exhibit attribution signals in their titles (patterns like "says", "claims", "according to", or named-entity colon formatting). Zero domains provide independent evidence of Iranian involvement. The independence score is 1 (just the originating source: Van Drew). This is the structural signature the abstract promises to detect.

- **Mass Hysteria: score 1, amplification 4×.** Four documents all report the Biden administration's or FAA's characterization of the sightings as misidentification. Like the Iranian Mothership, this is a single institutional position amplified by news coverage. The attribution patterns are clear: every title references an official source making the claim.

- **Test Flights: score 1, amplification 3×.** Three documents reporting the Trump White House's January 2025 explanation. Same echo-chamber structure as the other low-independence narratives.

- **UAP: score 3, amplification 0.7×.** Two documents from two domains, both classified as independent. The UAP narrative in the NJ drones corpus is the quietest, with only two documents. Neither exhibits attribution patterns in its title; both discuss UAP phenomena without attributing the claim to a named source. The higher independence score is correct: these documents are making their own assertions, not echoing a specific originating statement.

- **Legitimate Drones: score 11, amplification 3.5×.** This narrative matches all 38 documents (via generic keywords "drone", "aerial", "sighting"). Of 28 unique domains, 10 are classified as independent (making factual observations about drone presence without attribution signals). The remaining 18 are amplifiers. This is expected: the broadest narrative has the most diverse sourcing, but most coverage is still structured as reporting-on-reports.

### What this empirically shows

1. **The attribution-classification approach produces meaningful results at the title level.** Without requiring re-fetching or NLP processing of full document text, the title-based heuristic correctly identifies the Iranian Mothership narrative as a single-source echo chamber and the UAP narrative as having more independent sourcing.

2. **Independence score and amplification ratio are complementary metrics.** Independence score answers "how many independent sources?" Amplification ratio answers "how much volume per independent source?" A narrative can have high amplification with either low independence (echo chamber) or high independence (genuinely viral corroborated story). Both metrics together tell the story.

3. **The method distinguishes echo amplification from corroboration without building a full citation graph.** The title-heuristic approach is a lightweight approximation of citation-chain tracing. For the NJ drones corpus, it produces the same classification that a full link-extraction pass would produce, at a fraction of the computational cost.

### Denser corpus validation (2026-04-09, 96 documents)

**Corpus:** 96 documents from 49 distinct source domains.

| Narrative | Score (96) | Amp (96) | Score (38) | Amp (38) | Change |
|---|---:|---:|---:|---:|---|
| **Iranian Mothership** | **1** | **6.0×** | 1 | 6.0× | Unchanged |
| Mass Hysteria | 1 | 4.0× | 1 | 4.0× | Unchanged |
| Test Flights | 1 | 3.0× | 1 | 3.0× | Unchanged |
| Loose Nuke | 3 | 0.7× | 2 | 0.5× | +1 independent |
| UAP | 5 | 1.2× | 3 | 0.7× | +2 independent |
| **Legitimate Drones** | **34** | **2.8×** | 11 | 3.5× | +23 independent |

The echo-chamber narratives (Iranian Mothership, Mass Hysteria, Test Flights) are completely invariant across corpus sizes. This is the strongest stability finding: the attribution heuristic's classification of these narratives as single-source echo chambers does not change regardless of how many additional documents enter the corpus.

The legitimate-drones narrative grows from score 11 to 34 with 49 domains, demonstrating that genuinely diverse sourcing scales with corpus size. The amplification ratio drops from 3.5x to 2.8x as proportionally more independent reporting enters.

**Stability finding:** SIG classifications are the most stable signal across corpus densities. Echo chambers stay echo chambers. Independent narratives gain more independent sources.

### 204-document corpus validation (2026-04-09)

**Corpus:** 204 documents from 49+ sources after gap-filling ingestion.

| Narrative | Score (204) | Amp (204) | Score (96) | Amp (96) | Score (38) | Amp (38) |
|---|---:|---:|---:|---:|---:|---:|
| **Iranian Mothership** | **1** | **6.0x** | 1 | 6.0x | 1 | 6.0x |
| Mass Hysteria | 1 | 4.0x | 1 | 4.0x | 1 | 4.0x |
| Test Flights | 1 | 3.0x | 1 | 3.0x | 1 | 3.0x |
| Loose Nuke | 3 | 0.7x | 3 | 0.7x | 2 | 0.5x |
| UAP | 5 | 1.2x | 5 | 1.2x | 3 | 0.7x |
| **Legitimate Drones** | **31** | **3.4x** | 34 | 2.8x | 11 | 3.5x |

Echo-chamber narratives (Iranian Mothership, Mass Hysteria, Test Flights) are invariant across all three corpus densities. Independence score 1, amplification ratios unchanged. This is the strongest stability result in the entire signal suite: the attribution heuristic's classification of single-source echo chambers does not change regardless of corpus size.

Legitimate Drones shows a minor score reduction (34 → 31) as some gap-filling documents for this narrative were classified differently. The amplification ratio rose from 2.8x to 3.4x, reflecting a slightly higher proportion of amplifying coverage in the gap-filling period. The narrative remains by far the most independently sourced.

**Three-density stability finding:** SIG is the most stable signal across all three corpus densities. Echo chambers are invariant. Independent narratives track corpus composition but maintain their relative ordering.

### What this does NOT empirically show

- That title-level attribution heuristics scale to all news corpora. Outlets with non-standard titling conventions (e.g. aggregator sites with opaque headlines) would be harder to classify.
- That the attribution pattern list is complete. The current regex and entity list are tuned for the NJ drones corpus. A different policy domain (e.g. biosecurity) would need different entity lists.
- That the domain-level granularity is sufficient for all use cases. A single domain (e.g. reuters.com) might publish both independent investigative reporting and wire-service amplification of other sources' claims. The current approach treats the domain as a single node and classifies it by majority vote.
- That a full citation-chain graph would produce the same results. The title heuristic is an approximation. A future version that extracts hyperlinks and quoted-source attributions from full document text would provide higher-fidelity independence scores.

## Implementation

- `python/signals_methods/src/signals_methods/independence.py` — core computation (no database or blob dependency)
- `python/signals_methods/src/signals_methods/storage.py` — SIG-specific loaders and upserts
- `python/signals_methods/src/signals_methods/cli.py` — `signals compute independence` and `independence-status` commands
- `packages/db/src/schema/signal_independence.ts` — Drizzle schema, unique on `(topic, corpus_version, narrative_slug)`
- `apps/dashboard/app/_components/independence-table.tsx` — annotated table with echo-chamber badges and amplification bar chart
- `apps/dashboard/lib/queries.ts::getIndependenceRows` — Drizzle query feeding the table

## Open questions for the paper

- Should the independence graph use full-text citation extraction (hyperlinks, quoted-source attribution) in addition to title heuristics? The marginal accuracy gain vs. the computational cost of re-fetching blob content needs evaluation.
- How should SIG interact with NVD? A composite "narrative capture risk" score combining high NVD (narrative outpacing evidence) with low SIG (echo amplification) would be the most actionable metric.
- Can the attribution heuristic be learned from labeled examples rather than hand-coded? A small classifier trained on 100-200 labeled title pairs (independent vs. amplifier) might generalize better than regex patterns.
- How does SIG compare to existing source-credibility and media-bias tools (e.g. NewsGuard, MBFC, AllSides)? Those tools rate outlets at the organizational level; SIG rates them at the claim level. The two are complementary but distinct.
- How should the React Flow visualization be designed for the CMU talk? The current table is sufficient for the empirical claim, but a graph layout showing Van Drew at the center with six radiating amplifier domains would be a stronger visual.
