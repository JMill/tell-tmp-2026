# TELL Implementation Plan

**Status:** Approved 2026-04-06. Stage 2 completed and merged to main on 2026-04-08. See [`NEXT-STEPS.md`](NEXT-STEPS.md) for current phase and what's next.

**Provenance:** This is the canonical in-repo copy of the implementation plan that was approved via Claude Code's plan-mode workflow on 2026-04-06. The approval happened against a working copy at `/Users/jmill/.claude/plans/frolicking-swinging-map.md`, which lives outside the repository. That file is ephemeral and machine-local; this file is the authoritative record.

Any future revisions to the plan should be made here in the repo and captured in `admin/milestones/decisions.md` if they re-open decisions that the plan locks in.

---

# TMP 2026 Submission + TELL Pipeline Build

## Context

JMill is a Penn State D.Eng. student, currently chairless, building a praxis titled *"Sensemaking by Design: An Engineering Architecture for Anomaly Detection in Systems That Can't Afford to Be Wrong."* Professor Darryl Farber forwarded an opportunity to submit an abstract to the **CMU Technology, Management, and Policy (TMP) Graduate Consortium**, June 15-16, 2026 (abstract due April 23, 2026).

The submission is strategic: it is simultaneously a conference talk, a working artifact for the praxis defense, a demonstration of structured sensemaking methods tied to a live Lawfare policy piece and the CU26 academic paper, and a portfolio piece for recruiting a committee chair (Rothrock declined but is persuadable with strong work).

The build is an OSINT weak signal detection pipeline. It monitors information environments around ambiguous, high-uncertainty events using the November 2024 - January 2025 New Jersey aerial phenomena incident as the validation case study. Unlike prediction-oriented OSINT tools, it evaluates sensemaking *quality* rather than prediction accuracy. It introduces three novel data-driven methods — Information Vacuum Index (IVI), Narrative Velocity Divergence (NVD), and Source Independence Graph — alongside Bayesian hypothesis-evidence mapping derived from the CU26 paper's H1-H5 framework.

**Deliverables:**
1. **Abstract submission to CMU TMP** (April 23, 2026)
2. **Working demo at CMU** (June 15, 2026)
3. **Method documentation and retrospective results** suitable for citation in the praxis paper and for a standalone methods paper

## Decisions locked in

- **Tech stack**: Hybrid. Python owns the analysis pipeline. TypeScript/Next.js owns the dashboard and deploys to Vercel.
- **New top-level directories**:
  - `dev/` — new top-level for development projects that produce engineering artifacts
  - `dev/tell/` — the pipeline project (TELL: Totally Explainable, Looks Legit)
  - `engagements/` — new top-level for external commitments (conferences, talks, fellowship apps)
  - `engagements/2026-tmp-cmu/` — first engagement
- **Monorepo tooling**: pnpm workspaces for TS + uv workspaces for Python, both rooted in `dev/tell/`
- **Data stack**: Neon Postgres (via Vercel Marketplace) with pgvector for embeddings + Vercel Blob for raw documents
- **LLM orchestration**: AI SDK v6 + Vercel AI Gateway for interactive dashboard agent; anthropic Python SDK directly for offline batch classification
- **Visualization**: Visx (custom charts), React Flow (graph), shadcn/ui + Tailwind v4 with custom tokens (editorial-journal aesthetic, not generic AI template)
- **Retrospective scope for June 15**: offline batch Python runs against the NJ drones corpus; the dashboard reads precomputed results from Neon. No live ingestion on the critical path.
- **Abstract title** (JMill's draft, approved): *"Sensemaking under uncertainty: Engineering a human-machine pipeline for policy-relevant 'weak signal' detection"*
- **TMP form advisor**: Darryl Farber and Ling Rothrock both listed (updated 2026-04-06 after Farber's reply; original plan had Farber only)

## Build stages

Stages are sequential and gated by completion criteria, not calendar weeks. Actual pace is set by collaborative work sessions. The only hard dates are the abstract deadline (April 23) and the conference (June 15-16). Everything between is paced by progress.

Each stage should end with something independently demoable so the minimum viable demo is always one stage away. Dashboard work begins in Stage 2 with fixture data so design iteration runs in parallel with pipeline work from that point forward.

### Stage 0: Scaffolding + Ground Truth ✅ COMPLETED 2026-04-07

**Scope**: Approve and create `dev/tell/` and `engagements/` directories. Amend CLAUDE.md, fix STATUS.md, write decision log entry. Scaffold pnpm + uv workspaces. Provision Neon Postgres and Vercel Blob via Marketplace. Hand-curate the NJ drones ground-truth `timeline.yaml` (the single load-bearing document). Write seed URL list. Stub pydantic models and Drizzle schema.

**Gate**: `uv run signals --help` exits 0. `timeline.yaml` committed with 30+ canonical events and narrative tags, reviewed by JMill. `vercel link` succeeds. Neon database provisioned. CLAUDE.md/STATUS.md corrections committed.

**Status**: Infrastructure complete. `timeline.yaml` is a stub with one illustrative placeholder event — JMill's hand-authoring of canonical events is still outstanding and moves into Phase A below.

### Stage 1: Abstract Submission to CMU (in progress)

**Scope**: Finalize the abstract text (already drafted). Create `engagements/2026-tmp-cmu/submission/` with the abstract, form fields, and bio. Send Farber the response email asking for advisor listing permission. Submit the CMU form by April 23 (hard deadline). Capture confirmation.

**Gate**: Form submitted. Confirmation email received and filed at `engagements/2026-tmp-cmu/submission/submission-confirmation.md`.

**Status**: Abstract drafted and committed. Farber replied approving the advisor listing. JMill action items remaining: answer Farber's courses question, send Rothrock heads-up, verify Rothrock email, submit form.

### Stage 2: Layer 0 — Ingestion + Dashboard Scaffold ✅ COMPLETED 2026-04-08 (PR #3)

**Scope**: Implement ingestion adapters in priority order (Wayback/archive.org, Reddit archive, Congressional Record, AARO, arXiv). Checkpointed fetch, trafilatura extraction, Blob storage for raw, Neon for metadata. In parallel: scaffold `apps/dashboard/` with Next.js 16, Tailwind, shadcn, Drizzle, basic layout. One fixture query rendering document count.

**Gate**: `uv run signals ingest --since 2024-11-01 --until 2025-01-31` produces initial corpus (~2k documents) in Neon and Blob. Dashboard renders document count and a raw list page with filters.

**Status**: Infrastructure and vertical slice complete. One Wayback adapter works end-to-end. The original gate (2k documents, batch ingestion, multiple adapters) is not met; those move into Phase A below. The Stage 2 shipped as a vertical slice rather than horizontal coverage, which was the right call for proving the architecture but leaves the corpus-building work in front of us.

### Stage 3: Layer 1 — Classification + Design Tokens

**Scope**: Finish ingestion to target ~5-10k documents. Dedup pass. Embeddings via AI Gateway with HNSW index. Pilot hypothesis scoring on 500 documents to validate prompts, then scale to full corpus. Source reliability scoring via the SAT framework from the Lawfare piece. Dashboard: first real timeline view (Visx stacked bars by source kind). Define the editorial design tokens (palette, type scale, spacing) in `packages/ui/src/tokens/`.

**Gate**: Full corpus ingested, embedded, classified. `document_hypothesis_scores` populated. `sources.reliability_score` populated. Dashboard timeline page renders real data. Design tokens file committed with agreed palette/typography.

### Stage 4: Layer 2 — Weak Signal Methods

**Scope**: Implement the three novel contributions in `python/signals_methods/`:
1. **IVI** (Information Vacuum Index) with concrete definition of "authoritative response" (government publications matching topic keywords within window)
2. **NVD** (Narrative Velocity Divergence) with narrative clustering via HDBSCAN on embeddings and rolling derivatives
3. **Source Independence Graph** via networkx over citation edges extracted during ingestion

Dashboard: IVI gauge, NVD divergence chart (bespoke Visx), Source Independence Graph (React Flow + ELK layout with custom nodes). Second design pass on typography, motion, spacing.

**Gate**: All three signals firing against the NJ drones corpus. Cross-reference with ground truth: IVI spikes during the Dec 2024 vacuum window. NVD fires on the Iranian Mothership narrative within hours of the Van Drew press statement. Source Independence Graph reveals the echo-chamber topology showing ~20 articles tracing back to Van Drew.

### Stage 5: Layer 3 — Sensemaking Interface

**Scope**: Klein-activities-shaped agent loop in `packages/ai/` using AI SDK v6 `streamObject` and tool calling. Tools: `getDocuments`, `getHypothesisDistribution`, `getSignalFirings`, `explainNarrative`, `compareEvidence`. Six-tab interface (Elaborating, Questioning, Connecting, Comparing, Framing, Re-Framing) with streamed evidence cards. Cache Components for stable signal panels.

**Gate**: JMill can ask "what evidence contradicts the Iranian Mothership narrative?" and get a streamed answer with cited documents and linked timeline positions.

### Stage 6: Layer 4 — Evaluation

**Scope**: Sensemaking Quality Metrics against the ground-truth timeline in `python/signals_eval/`:
- Hypothesis coverage (did all H1-H5 stay above a floor until evidence warranted collapse?)
- Evidence-narrative alignment (when narrative diverged from evidence, did NVD fire?)
- Update responsiveness (lag from ground-truth event to signal firing)
- Premature closure resistance (did the system maintain uncertainty until the Jan 2025 public explanation?)

Dashboard evaluation page with scorecard and narrative explanations. Method docs written at `docs/methods/{ivi,nvd,independence,sqm}.md` for paper citation. Figure exports to `docs/figures/` for the paper and talk.

**Gate**: End-to-end walkthrough of NJ drones retrospective with sensemaking quality scorecard. Method docs committed. Figures exported.

### Stage 7: Polish + Talk Prep

**Scope**: Demo rehearsal with scripted click-through. Pin production deploy to a frozen Neon branch (e.g. `tmp-cmu-frozen-<date>`) so nothing changes under the presenter. Final typography and motion pass. Slides at `engagements/2026-tmp-cmu/talk/slides-vN.md`. Backup demo video recorded.

**Gate**: Dress rehearsal complete. Frozen Neon branch live. Slides pass-around ready. Backup video in place.

### Stage 8: Delivery (June 15-16)

**Scope**: Travel. Deliver the talk at CMU. Capture audience questions, contacts, retrospective at `engagements/2026-tmp-cmu/post/`.

**Gate**: Talk delivered. Post-event notes filed. `STATUS.md` updated with what happened.

## Abstract text (296 words, submitted to CMU)

Title: **Sensemaking under uncertainty: Engineering a human-machine pipeline for policy-relevant 'weak signal' detection**

> How should democratic governments manage information environments around ambiguous, high-uncertainty events that involve unresolved scientific and technical questions? The 2024 New Jersey aerial phenomena incident demonstrated the stakes. Thousands of witnesses, over 5,000 FBI tips, contradictory statements from FAA, DoD, and DHS, and no authoritative explanation produced an information vacuum that competing narratives filled within hours. An unverified "Iranian Mothership" claim from a congressman dominated news cycles. A "loose nuke" theory from a podcast migrated to mainstream media. Neither was supported by available evidence. Each shaped public response, from citizens firing weapons at the sky to FAA-reported laser strikes on commercial aircraft.
>
> This research presents an open-source intelligence pipeline that applies structured analytical techniques to discourse around ambiguous phenomena. The pipeline ingests government publications, legislative activity, news, social media, academic preprints, and aviation safety reports. It introduces three novel data-driven methods: an Information Vacuum Index quantifying the gap between public discourse and institutional response; Narrative Velocity Divergence flagging when narratives outpace evidence; and a Source Independence Graph distinguishing corroboration from echo amplification. The architecture embeds sensemaking theory (Klein, 2007) and systems-theoretic accident modeling (Leveson, 2012) as design requirements for human-machine collaborative evaluation.
>
> Retrospective analysis against the New Jersey incident shows the pipeline surfaces contradicting evidence within hours of dominant narratives emerging, maintains structured uncertainty across competing hypotheses, and flags conditions conducive to narrative capture. Unlike prediction-oriented OSINT tools, the system evaluates sensemaking quality rather than accuracy.
>
> The approach informs technology policy across domains where institutions must manage discourse around uncertain events: biosecurity incidents, emerging technology governance, critical infrastructure failures, and algorithmic amplification. It demonstrates how engineering architectures can support, rather than replace, democratic deliberation under uncertainty.

See [`abstract-claims.md`](abstract-claims.md) for a claim-by-claim map from this abstract to the code that must back each claim.

## Risks and mitigations

- **Ground-truth timeline quality** — the whole evaluation hinges on it. **Mitigation:** hard deliverable for Phase A in NEXT-STEPS.md; JMill personally authors; two-pass refinement.
- **Retrospective data availability** (social media archives for late 2024 are uneven). **Mitigation:** lean on Wayback + GDELT for news; accept imperfect social coverage; name as limitation in paper.
- **LLM cost overrun** beyond the $50-200 estimate. **Mitigation:** aggressive hash-based caching at `(document_hash, prompt_hash)` level; 500-doc pilot before full runs; AI Gateway cheapest capable model first.
- **Two-language schema drift** between pydantic and zod. **Mitigation:** automate sync in CI; schemas-in-sync job fails PRs on drift.
- **Vercel infra learning curve** (Next.js 16 Cache Components, AI SDK v6, Workflow all relatively new). **Mitigation:** keep Vercel surface area minimal through Stage 3; introduce Cache Components in Stage 4-5 only where load demands; skip Workflow entirely unless live ingestion is needed post-June.
- **Aesthetic fails to land** (ships looking like a Vercel template). **Mitigation:** design tokens are a hard gate for Stage 3 completion; dedicated design session with JMill early in Stage 3; no deferring aesthetic decisions to Stage 7 polish.
- **Python deployment ambiguity** eating days. **Mitigation:** firm commitment that Python runs offline (laptop + CI) for the TMP demo. Any Vercel Python Function story is post-June.
- **June 15 hard deadline with no slack.** **Mitigation:** every stage is independently demoable. The minimum viable demo (see below) is achievable once Stage 4 is partially complete — a single page showing the NJ drones timeline with IVI layered over it, pulled from a precomputed parquet file, plus the paper-ready method docs.
- **Zero empirically-validated abstract claims as of 2026-04-08.** The pipeline technically runs; the science has not been tested. **Mitigation:** the confidence plan in `NEXT-STEPS.md` prioritizes validating each abstract claim against the NJ drones corpus, starting with IVI as the easiest-to-defend novel contribution.

## Minimum viable demo (safety net)

If we can't complete all stages before June 15, the defensible demo at CMU is:
1. Static retrospective report: one-page hero Visx timeline with IVI (and NVD if completed), pulled from precomputed parquet loaded at build time
2. One working signal: IVI is easiest to compute and explain
3. Method docs at `dev/tell/docs/methods/{ivi,nvd,independence,sqm}.md` demonstrating the research contribution even if the interactive artifact is thin
4. A recorded demo video as backup if the live site breaks

This minimum maps to completing Stage 4 (at least IVI portion) plus the written method docs. Everything from Stage 5 onward is upside.
