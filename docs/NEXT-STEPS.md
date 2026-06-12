# Next Steps

**Last updated:** 2026-04-09 (204-doc corpus, gap-filling complete, NVD threshold recalibrated)
**Current phase:** Phase E complete. 204-document corpus with gap-filling. All methods validated across three corpus sizes. Next: talk prep and remaining claim polish.

Phases A through E are complete. The corpus now has 204 documents from 49+ sources (up from 38 → 96 → 204 docs across three builds). All three novel methods are implemented, computed, and validated at all three corpus densities. Gap-filling ingestion added coverage for Jan 3, 5, 10, and 28, reducing the formerly empty Dec 21 - Jan 28 void. NVD composite threshold recalibrated from 1.5 to 1.1 to account for ratio compression at higher corpus density.

**Six of eight abstract claims are now 🟢 validated (multi-source ingestion, IVI, NVD, SIG, structured uncertainty, narrative-capture flagging). Two are 🟡 partial (contradicting evidence, Klein/Leveson design requirements). Zero rhetorical or unproven.**

This file is the single "what's next?" pointer. If you're picking up the work (future-JMill, a collaborator, or a new AI agent session), read `getting-started.md` for how the system works today, then read this file to understand what to do next. For the full long-range plan see `plan.md`.

## The governing question

**Can the pipeline actually do what the CMU abstract promises, against real data?**

As of 2026-04-09 the answer is: mostly yes. The infrastructure works end-to-end (Wayback → trafilatura → Blob + Neon → Drizzle → Next.js dashboard). All three novel methods are implemented and validated against the NJ drones corpus at two corpus densities (38 and 96 documents). The SQM evaluation framework produces reproducible empirical results. See `abstract-claims.md` for a claim-by-claim status. Six of eight claims are empirically validated, two are partially demonstrated.

The priority for remaining work between now and June 15 is **tightening the 🟡 partial claims toward 🟢** (targeted gap-filling ingestion for Claim 6, Klein/Leveson interactive interface for Claim 5) and **talk preparation** (method docs, figures, demo script). The sequencing below is complete through Phase E; remaining work items are listed in the cross-cutting section.

## Hard dates

- **2026-04-23** — CMU TMP abstract submission deadline. Stage 1 (not in this file; tracked in `engagements/2026-tmp-cmu/`).
- **2026-06-15** — CMU TMP talk day. Pipeline demo and claims must be defensible.

## Phases

Phases are sequential and gated by empirical results, not calendar weeks. Each phase ends with something you can demo and something you can write down as a defensible claim.

### Phase A — Build a real NJ drones corpus (current phase)

**Why this first:** Every downstream method (IVI, NVD, Source Independence Graph, hypothesis scoring) needs more than one document. The current corpus has two documents. Nothing is testable until this is fixed. This is also the lowest-technical-risk phase — it's pattern extension of the Wayback adapter, not new algorithms.

**Scope:**

1. **Populate `data/nj-drones/seed-urls.yaml`** with 50-100 verified URLs from `data/nj-drones/research/2026-04-07-verified-events.md`. Format: one URL per entry with source kind, approximate date, and narrative tags where applicable. This is a ~1 hour mechanical task but needs JMill's judgment on which events to canonicalize.

2. **Author `data/nj-drones/timeline.yaml`** properly. The current file is a stub with one illustrative placeholder event. Target: 30-50 canonical events hand-curated by JMill from the research dossier. Do NOT delegate canonical dates to LLMs — timeline is the ground truth for evaluation. This is the single load-bearing artifact for the whole evaluation framework.

3. **Implement batch ingestion**: add `signals ingest batch --corpus <name> --seeds <path>` that reads the seed URLs file, dedupes, and pipelines each entry through the existing `signals_ingest` adapters. Respect rate limits. Log progress and failures.

4. **Add at least one more adapter** beyond Wayback. Candidates in priority order:
   - **Reddit pushshift-equivalent** (or just Wayback over Reddit thread URLs if pushshift is unavailable)
   - **Congressional Record** via the govinfo.gov API
   - **FBI/DHS/FAA official statements** via Wayback on their press release pages
   - **arXiv** for UAP-adjacent preprints
   Each adapter is ~80-150 lines following the Wayback pattern at `python/signals_ingest/src/signals_ingest/adapters/wayback.py`.

5. **Run the batch** against the full seed list. Target: 50+ documents in Neon from at least 10 distinct sources covering the November 2024 - January 2025 window.

**Gate:**
- Dashboard shows a real corpus: ≥50 documents, ≥10 sources, at least one document per day of December 2024
- `timeline.yaml` has ≥30 canonical events
- `seed-urls.yaml` has ≥50 entries with source kind and date annotations
- Rerunning the batch command is idempotent (verified in Stage 2: the unique index on `(source_id, url, corpus_version)` handles this)

**What this unlocks:** everything downstream. Phase B (IVI) needs real volume to compute anything meaningful. Phase C (hypothesis scoring) needs the documents to score. Phase D (NVD, Source Independence Graph) needs the corpus plus the scored hypotheses.

### Phase B — Implement and validate IVI

**Why this next:** IVI is the simplest of the three novel methods, depends only on document counts and source-type classification (which we already have), and is the easiest-to-defend claim in the abstract. If IVI works against the NJ drones corpus, we have empirical backing for one of three novel contributions. If it doesn't work, we need to know that now, not in June.

**Scope:**

1. **Write `python/signals_methods/` as a new workspace package.** Follow the scaffolding pattern of `signals_core` and `signals_ingest`: `pyproject.toml`, `src/signals_methods/__init__.py`, `README.md`.

2. **Implement `ivi.py`** with the simplest honest definition that matches the method doc at `docs/methods/ivi.md`:
   ```python
   # Pseudocode
   def ivi(
       topic: str,
       window_start: datetime,
       window_end: datetime,
       *,
       discourse_sources: set[SourceKind] = {NEWS, SOCIAL, FORUM, PODCAST},
       authoritative_sources: set[SourceKind] = {GOV, ACADEMIC, AVIATION},
   ) -> float:
       discourse = count_docs(topic, window_start, window_end, source_kind__in=discourse_sources)
       authoritative = count_docs(topic, window_start, window_end, source_kind__in=authoritative_sources)
       return discourse / (authoritative + 1)
   ```
   Start with daily windows. Add configurable smoothing later if needed.

3. **Add a `signal_ivi` table** to the Drizzle schema (and mirror in pydantic) to persist the time series: `(topic, window_start, window_end, value, discourse_count, authoritative_count)`.

4. **Implement `signals compute ivi --topic nj-drones --corpus nj-drones-2026-04-07`** CLI command that runs IVI over the full corpus and writes to the signal table.

5. **Render on the dashboard** as a Visx time series overlay on the existing document timeline. Hero view for the talk.

6. **Validate against ground truth**: does IVI spike during the December 2024 vacuum period (Dec 9-18 when discourse volume was highest and institutional response was lowest)? Cross-reference with `timeline.yaml` canonical events.

**Gate:**
- IVI computed over the full NJ drones corpus, persisted to Neon
- Time series rendered on the dashboard
- **Empirical result documented** in `docs/methods/ivi.md` under a new "Validation against NJ drones corpus" section, with the actual numbers and a characterization of whether the spike matched expectations
- If IVI doesn't match expectations: write up why, and decide whether to refine the method, change the source classification, or abandon it as a contribution. **This is the moment to know.**

**What this unlocks:** one empirically-defensible novel contribution. If IVI works, the CMU talk's central empirical claim is backed. Phase C can then focus on the remaining claims.

### Phase C — Implement H1-H5 hypothesis scoring

**Why:** The abstract claims the pipeline "maintains structured uncertainty across competing hypotheses." That requires actual hypothesis distributions derived from documents. It's also a prerequisite for NVD (which scores narratives against hypothesis-supported evidence).

**Scope:**

1. **Create `signals_analyze` workspace package** (new, parallel to `signals_ingest`).

2. **Implement `signals_analyze/hypothesis_scoring.py`** using batched Anthropic SDK calls with structured output via `instructor` or equivalent. Per-document: score each of H1-H5 in [0, 1] with a brief rationale. Cache aggressively on `(content_hash, prompt_version, model)`.

3. **Add `document_hypothesis_scores` and `hypothesis_distributions` tables** to the schema.

4. **Implement `signals analyze hypotheses --corpus nj-drones-2026-04-07 --pilot 50`** CLI command. Pilot on 50 documents to validate the prompt, then scale.

5. **Aggregate into `hypothesis_distributions` time series** per topic per day (entropy + mode + full distribution).

6. **Render on the dashboard**: stacked area chart showing H1-H5 evolving over time. Second hero view.

7. **Validate against ground truth**: do the distributions show the expected evolution? Specifically, does H5 (Unknown) and H4 (Classified Tech) stay non-zero throughout — i.e., does the system resist premature closure?

**Gate:**
- Hypothesis scores populated for ≥50 documents
- Hypothesis distribution time series rendered on the dashboard
- Empirical result documented in `docs/methods/sqm.md` under a "Hypothesis coverage observation" section

**What this unlocks:** second empirically-defensible novel contribution (the structured-uncertainty claim).

### Phase D — NVD and Source Independence Graph

**Why last:** Both depend on the corpus from Phase A and the hypothesis scoring from Phase C. NVD needs narrative clustering (HDBSCAN on embeddings, which also requires embeddings, which is Stage 3 scope). Source Independence Graph needs citation extraction during ingest, which may require retroactively reprocessing the corpus.

**Scope:**

1. **NVD**: implement `signals_methods/nvd.py`. Cluster documents via HDBSCAN on embeddings. Match clusters to narratives in `data/nj-drones/narratives.yaml`. Compute velocity as rolling derivative of narrative-document count. Compute evidence velocity as rolling derivative of hypothesis-supported evidence for that narrative. NVD = narrative velocity - evidence velocity.

2. **Source Independence Graph**: extract citation edges during ingestion (links, attributed quotes, named-source mentions). Retroactively process the existing corpus. Build graph with networkx. Compute independence score per claim/narrative via weakly-independent-component count.

3. **Dashboard views**: NVD divergence chart (Visx); Source Independence Graph (React Flow + ELK layout).

4. **Validate against ground truth**: does NVD fire on the Iranian Mothership narrative within hours of Van Drew's Dec 11 statement? Does the Source Independence Graph show the expected echo chamber topology?

**Gate:** all three methods firing against the corpus with documented empirical results per method.

### Phase E — Sensemaking Quality Metrics (SQM) evaluation ✅

**Completed 2026-04-08.** Four SQM metrics implemented in `python/signals_methods/src/signals_methods/eval.py`:

1. **Contradicting evidence lag** — Iranian Mothership: 0-hour lag (same-day Pentagon denial). Mass Hysteria: 1,128 hours (unchanged at 96 docs). Loose Nuke: no contradicting document found.
2. **Composite narrative-capture risk** — At 38 docs: two alerts (Dec 11 risk 4.80, Dec 13 risk 2.00). At 96 docs after temporal alignment fix: one alert (Dec 11, risk 2.20 with 3-day IVI windows).
3. **Evidence-narrative alignment** — 47 windows, 2 misaligned (95.7% aligned at 96 docs, up from 22 windows at 38 docs).
4. **Premature closure resistance** — 26 days analyzed. Min 57.4%, max 96.4% (Dec 11), mean 86.5%.

Moved Claim 6 from 🔴 to 🟡, Claim 8 from 🟡 to 🟢 (38-doc corpus), then 🟢→🟡 (96-doc corpus, temporal mismatch), then 🟡→🟢 (SSOT refactor, 3-day IVI for composite). Post-polish: Claim 1 🟡→🟢, Claim 3 🟡→🟢, Claim 4 🟡→🟢, Claim 5 ⚪→🟡. Six claims now 🟢, two 🟡, zero ⚪.

### Remaining work — Polish, gaps, and talk prep

These are not a sequential phase but a prioritized backlog. Each item directly serves either tightening a 🟡 claim toward 🟢 or preparing the June 15 talk.

**Claim gap closures:**
- ~~Fix loose-nuke keyword matching~~ ✅ (PR #12)
- ~~Source-kind reclassification fix~~ ✅ (PR #12)
- ~~SQM docs update~~ ✅ (PR #12)
- ~~Denser corpus ingestion~~ ✅ (96 docs from 101 seed URLs, 92 succeeded, 9 failed)
- ~~Recompute all signals on 96-doc corpus~~ ✅ (IVI, NVD, SIG, SQM all recomputed)
- ~~Klein/Leveson architecture-to-framework mapping document~~ ✅ (written as `docs/methods/framework-mapping.md`, Claim 5 moved ⚪→🟡)
- ~~Composite capture-risk threshold recalibration~~ ✅ (SSOT refactor: 3-day IVI for composite evaluation, Claim 8 restored 🟢)
- ~~Targeted gap-filling ingestion~~ ✅ (204-doc corpus, PR #18. Mass-hysteria lag 1,128 hours is a genuine information-environment finding.)
- ~~React Flow graph visualization for SIG~~ ✅ (echo-chamber topology graph added, PR #22)
- ~~Klein/Leveson sensemaking annotations on dashboard~~ ✅ (six-card grid mapping Klein activities + STAMP concepts to charts, Claim 5 strengthened)

**Method documentation:**
- ~~204-doc validation results added to all four method docs~~ ✅ (PR #20)
- Export figures for the paper and talk

**Talk preparation:**
- ~~Demo script~~ ✅ (`engagements/2026-tmp-cmu/talk/demo-script.md`, PR #20)
- ~~Slides outline~~ ✅ (`engagements/2026-tmp-cmu/talk/slides-v01.md`, PR #20)
- Pin production deploy to a frozen Neon branch
- Backup demo video

## Cross-cutting work that should happen alongside

These are not phases; they're ongoing hygiene. Fold into whatever phase you're in.

1. **Add tests.** There are zero tests today. Any new function in `signals_methods/` or `signals_analyze/` should land with at least one unit test. Set up a `tests/` directory under each Python package. Add `pnpm --filter @tells-fyi/db test` and `pytest` to a basic CI workflow.

2. **Script the smoke test.** The current smoke test lives in getting-started.md as a command to run by hand. Capture it as `scripts/smoke-test.sh` or a pytest integration test so regressions are visible.

3. **Document quirks as they emerge.** Getting-started.md has a "Quirks and gotchas" section with 7 entries from Stage 2. Add new quirks there as the codebase grows.

4. **Schema sync CI.** When adding schema tables, set up the pydantic → JSON Schema → zod drift check before the schema complexity gets out of hand.

5. **Design tokens.** The dashboard uses placeholder editorial-palette tokens. They need a dedicated session with JMill to lock the final palette, typography, and motion. Hard-gate before Phase B finishes (no point building Visx charts with the wrong tokens).

## JMill-only action items (not for AI agents)

These require JMill's personal judgment and cannot be delegated:

- [ ] Answer Prof. Farber's courses question (TMP correspondence thread)
- [ ] Verify Prof. Rothrock's email address before the TMP form submission
- [ ] Send the Rothrock heads-up email (draft staging needed) before submitting the TMP form
- [ ] Submit the CMU TMP Google Form by 2026-04-23
- [ ] Hand-author `data/nj-drones/timeline.yaml` canonical events (Phase A prerequisite)
- [ ] Make the Zenoh scope decision when Phase B concludes (see `research/frameworks/2026-04-07-zenoh-evaluation.md`)

## Decision log references

- `admin/milestones/decisions.md` — all locked-in decisions with rationale and date
- `research/frameworks/2026-04-07-zenoh-evaluation.md` — open option on Zenoh adoption
- `dev/tell/docs/plan.md` — full plan (this is the companion document)

## If you're a future AI agent picking this up

Read, in order:
1. `/CLAUDE.md` (repo root)
2. `STATUS.md`
3. This file
4. `dev/tell/docs/getting-started.md`
5. `dev/tell/docs/abstract-claims.md`
6. `dev/tell/docs/plan.md`
7. `dev/tell/CLAUDE.md` (subtree conventions)

That gives you the full picture. Then check `git log --oneline -20` and `git status` to understand what's happened recently. Then pick up the current phase above.

The single most important principle: **scientific confidence beats feature count**. Do not add new adapters or dashboard features unless they directly serve the current phase's gate. The CMU talk needs one thing — empirical backing for the abstract — and the deadline is real.
