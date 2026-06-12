# Phased Investigation Plan: February 2023 High-Altitude Objects

**Status:** Draft for JMill review
**Branch of origin:** `claude/investigate-2023-uap-incidents-sGPOX`
**Last updated:** 2026-04-19
**Owner:** JMill (canonical data authoring); Claude (drafting, ingestion, signal runs under supervision)

## 1. Context

TELL has demonstrated its weak-signal detection pipeline on a single case: the New Jersey drone incident of November 2024 through January 2025. One case is insufficient to validate the methods as generalizable. A second case with comparable structural features (ambiguous aerial phenomena, institutional uncertainty, narrative contention) tests whether the Information Vacuum Index, Narrative Velocity Divergence, Source Independence Graph, and Sensemaking Quality Metrics behave as theory predicts outside the conditions they were developed against.

The February 2023 cluster of high-altitude object events is the strongest available second case. Over roughly two weeks the United States shot down four airborne objects, an unprecedented concentration that strained detection infrastructure, interagency coordination, and public communication. Four of the five episodes are exceptionally well-documented in primary sources (DoD transcripts, NORAD statements, White House readouts, FBI forensic updates). The anomalous-objects phase on February 10, 11, and 12 is the empirical payoff: three intercepts of small, slow, low-signature objects whose origins were never physically confirmed and whose official attribution was downgraded by the White House within 72 hours of the last shootdown.

This investigation has two goals. First, produce a frozen corpus and canonical timeline that the existing TELL pipeline can score end-to-end. Second, compare signal behavior across the two cases and write a short method memo per signal that reports per-narrative numbers alongside the NJ drones equivalents. The output feeds Phase E claim validation in `docs/abstract-claims.md`.

## 2. Investigation boundaries

**In scope.** January 28, 2023 through June 29, 2023. The opening bound covers first North American radar detection of the PRC balloon. The closing bound covers the DoD forensic attribution statement that confirmed the balloon's SIGINT-collection payload. A secondary hook extends to the Office of the Director of National Intelligence UAP annual report published in October 2023, which retrospectively incorporated the February cluster into the official UAP data set.

**Out of scope.** General UAP policy history, the 2004 Nimitz encounters, the 2017 New York Times reporting, the 2021 and 2022 ODNI preliminary assessments, and the broader 2023 congressional UAP hearings beyond direct references to the February incidents. The NJ drone case is also out of scope for this investigation; cross-case analysis lives in a separate method-memo deliverable.

## 3. Phases

The phases are sequenced by dependency. Phase 0 gates Phases 1, 2, and 3. Phases 1 through 3 can advance partially in parallel once the ground-truth dossier stabilizes. Phase 4 gates Phase 5. Phase 6 is independent and may proceed at any time.

---

### Phase 0. Ground-truth dossier

**Deliverables.**

- `research/2026-MM-DD-verified-events.md`: hand-curated verified events document modeled on `dev/tell/data/nj-drones/research/2026-04-07-verified-events.md`. One section per verified event, each with category, narratives tagged, evidence weight, summary, primary-source URLs, and notes.
- `research/2026-MM-DD-fourth-fifth-object-anomalies.md`: dedicated dossier on the Lake Huron shootdown and the Montana radar-anomaly closure. Sections on radar signatures as disclosed by NORAD, shootdown engagement kinematics, unrecovered wreckage implications, pico-balloon overlap analysis with the Northern Illinois Bottlecap Balloon Brigade K9YO-15 tracking data, Montana airspace-closure sequence, hypothesis-by-hypothesis scoring against the H1-H5 framework, and open questions.

**Acceptance criteria.**

1. Every factual claim has at least one primary-source URL attached, or carries a `[CITE-NEEDED]` marker.
2. No invented URLs. No LLM-synthesized dates. Dates come from named press releases, hearing transcripts, or tier-1 news reports.
3. JMill reads and annotates both documents. Annotations resolved before Phase 1 begins.
4. Writing-rules compliance: no em-dashes, no hedging, no physical metaphors for non-physical concepts, active voice.

**Effort estimate.** One working session for the verified-events draft, one half-session for the anomalies dossier, JMill review loop.

**Approval gate before Phase 1:** yes.

---

### Phase 1. Narrative definitions

**Deliverable.** `narratives.yaml` at the investigation root, schema-identical to `dev/tell/data/nj-drones/narratives.yaml`. Fields per narrative: `slug`, `label`, `category`, `hypothesis`, `hypothesis_id`, `keywords`, `first_seen`, `originating_source`, `claim`, `evidence_weight`, `notes`.

**Draft narrative slugs.**

| slug | hypothesis_id | claim summary | originating source |
|------|---------------|----------------|---------------------|
| `prc-surveillance` | H4 (foreign adversary, China) | PLA Strategic Support Force high-altitude ISR program; balloon carried SIGINT gear | DoD briefings Feb 2 onward; FBI Quantico forensic statement Jun 29 2023 |
| `prc-civilian-weather` | H3 | Civilian meteorological research airship blown off course | PRC Ministry of Foreign Affairs statement Feb 3 2023 |
| `hobbyist-pico-balloon` | H3 | Amateur pico-balloon (NIBBB K9YO-15) explains the Yukon intercept | Aviation Week and NIBBB statement Feb 16 2023 |
| `classified-us-tech` | H4 (USG developmental) | USG or contractor test asset | online speculation; analysis in trade press |
| `uap-unknown` | H5 | Residual non-attributable phenomena | UAP-community commentary |
| `misidentification-threshold` | H1 | NORAD radar sensitivity adjustment after Feb 4 produced spurious tracks | NORAD briefings Feb 12-13 2023 |
| `adversary-black-tech` | H4 (foreign adversary, Russia or other) | Non-China adversary craft tested in Arctic ADIZ | online forums |
| `official-recreation-research` | H3 | Biden administration attribution to private, recreational, or research entities | White House press briefing Feb 14 2023 |

**Acceptance criteria.**

1. Every slug backs a real public claim with a named originator and a linkable primary source.
2. Every narrative maps to exactly one `hypothesis_id` in `dev/tell/data/hypotheses.yaml`.
3. Keyword lists are drawn from verbatim language appearing in the corpus. No invented keywords.
4. `evidence_weight` follows the existing enum: `strong`, `moderate`, `weak`, `rumor`.

**Effort estimate.** Half-session drafting, JMill review loop.

**Approval gate before Phase 2:** yes.

---

### Phase 2. Canonical timeline

**Deliverable.** `timeline.yaml` at the investigation root, schema-identical to `dev/tell/data/nj-drones/timeline.yaml`. Metadata block with `corpus: high-altitude-objects-2023`, `window_start: 2023-01-28`, `window_end: 2023-07-31`, `authored_by: JMill (with Claude research support)`, `source_dossier: research/2026-MM-DD-verified-events.md`, `version: 0.1.0-draft`.

**Target event count.** 30 to 50 events across four temporal clusters.

1. Balloon phase, Jan 28 through Feb 5. First radar detection; Canadian airspace transit; first public sighting over Billings, Montana; DoD and NORAD press briefings; Blinken postpones Beijing trip; FAA ground stops over the Carolinas; F-22 Sidewinder shootdown off Surfside Beach.
2. Anomalous-objects phase, Feb 10 through Feb 12. Alaska object shootdown near Deadhorse; Yukon object shootdown under joint US-Canadian authorization; Montana radar-anomaly and airspace closure; Lake Huron F-16 shootdown. Required detail on miss-and-re-engage at Lake Huron per SecDef Austin.
3. Official communications phase, Feb 12 through Feb 17. VanHerck NORAD press conference; Kirby White House briefing attributing objects to private, recreational, or research entities; Biden formal address on Feb 16; Pentagon confirmation of no recovered wreckage for the three anomalous objects.
4. Oversight and forensic phase, Feb 13 through Jun 29. Senate and House closed briefings; H.Res.104 resolution condemning PRC surveillance; House Select Committee on the CCP formation statements; FBI Quantico preliminary and final forensic statements; DoD confirmation that the balloon carried SIGINT-collection gear.

**Acceptance criteria.**

1. Every event has at least one source URL. Prefer primary sources.
2. `narratives:` tag set restricted to slugs defined in `narratives.yaml`.
3. `category:` drawn from the existing enum: `observation`, `institutional-statement`, `media-coverage`, `policy-action`, `narrative-claim`, `evidence`, `other`.
4. `evidence_weight:` from the existing enum: `strong`, `moderate`, `weak`, `rumor`.
5. JMill audits canonical dates against primary sources. No LLM-generated canonical dates.
6. Cross-reference integrity: every `narratives:` entry resolves to a slug in `narratives.yaml`.

**Effort estimate.** One working session drafting, one JMill review loop.

**Approval gate before Phase 3:** no. Phase 3 can begin with Phase 2 in draft.

---

### Phase 3. Seed URL list

**Deliverable.** `seed-urls.yaml` at the investigation root, schema-identical to `dev/tell/data/nj-drones/seed-urls.yaml`. Fields per seed: `url`, `source_kind`, `adapter`, `event_date`, `narratives`, `notes`.

**Target seed count.** 80 to 120 URLs.

**Distribution target.**

- Government (~30): war.gov (successor host to defense.gov) press releases and transcripts; norad.mil; 2021-2025.state.gov readouts; bidenwhitehouse.archives.gov Biden Feb 16 remarks and Kirby Feb 13-14 briefings; FBI press; FAA NOTAM archive; congress.gov H.Res.104; Senate Intelligence and Armed Services committee records; House Select Committee on the CCP records; CRS Insight IN12118 "Monitoring the Sovereign Skies" by Bart Elias (Feb 27 2023) and any adjacent CRS products located during seed curation; ODNI 2023 UAP annual report; Canadian Department of National Defence and Privy Council Office statements; RCAF press.
- News tier-1 (~25): New York Times, Washington Post, Reuters, Associated Press, CNN, BBC, CBC.
- Aviation and trade press (~15): The War Zone, Aviation Week, Breaking Defense, Air and Space Forces Magazine.
- Academic and think-tank (~10): CSIS (Bonny Lin), Brookings, RAND, Stimson, Atlantic Council.
- Forum and social (~8): NIBBB pico-balloon statement page; WSPR amateur-radio tracker archives; archived Reddit threads tagged to `uap-unknown` and `hobbyist-pico-balloon`.
- Podcasts (~5): War on the Rocks, Lawfare, Defense and Aerospace Report.
- Other (~5): Wikipedia navigational indexes for the PRC balloon incident and the high-altitude object events, as reference pointers only.

**Adapter routing.**

- `direct` for gov sources and stable PDF permalinks.
- `wayback` for news sources to stabilize against paywall and content drift.

**Acceptance criteria.**

1. Every seed maps to at least one event date and at least one narrative slug from `narratives.yaml`.
2. No fabricated URLs. Every URL must return a real document on at least one adapter.
3. `source_kind:` drawn from the existing enum: `gov`, `news`, `social`, `academic`, `aviation`, `forum`, `podcast`, `other`.
4. File passes YAML parse and schema-field parity check against `dev/tell/data/nj-drones/seed-urls.yaml`.

**Effort estimate.** One working session drafting, URL verification pass, JMill sign-off.

**Approval gate before Phase 4:** yes.

---

### Phase 4. Corpus ingestion

**Deliverable.** A frozen corpus version named `high-altitude-objects-2023-YYYY-MM-DD` in Vercel Blob and Neon Postgres, produced by the existing `signals ingest batch` command.

**Command shape.** The `batch` subcommand accepts `--corpus` and `--seeds` only; the corpus version string is what scopes the run.

```
uv run signals ingest batch \
  --corpus high-altitude-objects-2023-YYYY-MM-DD \
  --seeds dev/tell/data/high-altitude-objects-2023/seed-urls.yaml
```

**Acceptance criteria.**

1. At least 90 documents successfully ingested.
2. At least five distinct source kinds represented.
3. Ingestion failure log captured and committed to `research/YYYY-MM-DD-ingestion-run.md`, including per-URL error codes and whether each failure was retried on the alternate adapter.
4. `signals ingest status --corpus high-altitude-objects-2023-YYYY-MM-DD` reports a document count matching the success count, confirming Neon `source` and `document` rows and Vercel Blob objects for the corpus version. Signal tables (`signal_ivi`, `signal_nvd`, `signal_independence`) are not populated at this phase; they are the Phase 5 deliverable.

**Effort estimate.** One working session for the run and failure-log write-up.

**Approval gate before Phase 5:** yes.

---

### Phase 5. Signal computation and method memos

**Prerequisite: resolved.** The `--narratives` CLI flag is wired through `signals compute nvd`, `signals compute independence`, and `signals compute eval`. The module-level loader exposes `find_narratives_yaml(topic=...)` and `load_narrative_defs(path)` as the public API. The module-level `NARRATIVE_DEFS` default remains the nj-drones walk-up so existing runs stay backward-compatible. See test coverage at `python/signals_methods/tests/test_narratives_loader.py`.

For Phase 5 runs against this investigation, pass the explicit path:

```
--narratives data/high-altitude-objects-2023/narratives.yaml
```

Omitting `--narratives` will load the nj-drones defaults and produce garbage cross-case metrics, so every Phase 5 run against this corpus must pass the flag.

**Deliverables.**

- Signal values computed and stored under the new topic: IVI, NVD, SIG, SQM.
- `docs/methods/results/2026-MM-DD-ivi-high-altitude-objects-2023.md`: results memo for Information Vacuum Index, including per-day values across the investigation window, peak value and peak date, and a side-by-side row against the NJ drones peak (IVI 17.0 on Dec 24 2024).
- Equivalent result memos for NVD, SIG, and SQM.
- A short cross-case synthesis memo: `docs/methods/results/2026-MM-DD-cross-case-synthesis.md` summarizing where the signals behaved as theory predicted and where they diverged.

**Acceptance criteria.**

1. Each memo reports specific numerical values, not qualitative assertions.
2. Each memo cites the exact timeline events that co-occur with signal peaks and troughs.
3. The cross-case synthesis explicitly states whether the Phase E claims in `dev/tell/docs/abstract-claims.md` strengthen, weaken, or stay unchanged with the second case added.
4. Writing-rules compliance throughout.

**Effort estimate.** Two working sessions: one for runs and numerical capture, one for memo drafting.

**Approval gate before Phase 6:** no. Phase 6 is independent.

---

### Phase 6. Dashboard integration (follow-up, not blocking)

**Deliverable.** Topic toggle at `dev/tell/apps/dashboard/app/page.tsx` replacing the hardcoded `DEFAULT_TOPIC = "nj-drones"` at lines 15-16 with a topic-aware route or selector backed by a topic registry.

**Shape.** Likely `app/[topic]/page.tsx` with a registry mapping `nj-drones` and `high-altitude-objects-2023` to their corpus identifiers.

**Acceptance criteria.**

1. Both investigations render side by side from the same dashboard code path.
2. All existing NJ drones dashboard behavior preserved.
3. No new hardcoded topic strings anywhere in the app directory.

**Effort estimate.** One working session.

**Approval gate before anything else:** no. This phase is independent and can be scheduled when dashboard work fits the sprint.

## 4. Cross-phase guardrails

**Writing rules.** All prose across all phases follows `dev/tell/CLAUDE.md`: no em-dashes, no hedging words, no physical analogies for non-physical concepts, active voice, precise and confident and specific. `[CITE-NEEDED]` marks unverified claims.

**Canonical-data authoring gate.** JMill personally audits every canonical date in `timeline.yaml` and every narrative definition in `narratives.yaml` against primary sources before any Phase 5 memo cites those values. This mirrors the NJ drones authoring protocol.

**Schema parity.** Every YAML file in this investigation mirrors the field set of the corresponding NJ drones file. No invented fields. Schema drift is caught by a pre-merge grep of field names.

**Narrative-reference integrity.** Every `narratives:` entry in `timeline.yaml` and `seed-urls.yaml` resolves to a `slug:` in `narratives.yaml`. Pre-merge grep catches violations.

**Hypothesis-reference integrity.** Every `hypothesis_id:` in `narratives.yaml` is one of `H1`, `H2`, `H3`, `H4`, `H5`, matching `dev/tell/data/hypotheses.yaml`.

## 5. Dependencies and sequencing

```
Phase 0 (ground-truth dossier)
  -> Phase 1 (narratives.yaml)    <-+
  -> Phase 2 (timeline.yaml)      <-+  (Phases 1-3 advance in parallel once 0 stabilizes)
  -> Phase 3 (seed-urls.yaml)     <-+
        -> Phase 4 (corpus ingest)
            -> Phase 5 (signal runs + memos)

Phase 6 (dashboard) is independent and may proceed in parallel with any other phase.
```

## 6. Risks and open questions

1. **Canonical-date review latency.** JMill is the authoring gate. If review loops stall, Phase 2 and downstream phases stall.
2. **Montana "fifth object" status.** No physical object was ever confirmed. The event is a NORAD airspace closure with no intercept. The investigation treats it as a first-class event because the closure itself is the signal, but the framing in the dossier must be precise.
3. **Pico-balloon attribution for the Yukon object.** NIBBB's missing K9YO-15 is the most plausible public attribution for the Feb 11 Yukon intercept. No official US or Canadian government statement has adopted this attribution. The `hobbyist-pico-balloon` narrative has moderate evidence weight at best and must not be elevated in the absence of official corroboration.
4. **Dashboard refactor scope creep.** Phase 6 may pull in wider multi-investigation routing work. Keep scope tight and defer broader registry work to a separate plan.
5. **Corpus availability.** Some Feb 2023 tier-1 news articles now live behind paywalls with aggressive anti-Wayback blocks. Expect ingestion failure rates above the NJ drones baseline. Phase 4 acceptance criteria account for this.

## 7. Deliverable file inventory

When all phases land, the investigation directory will contain:

```
dev/tell/data/high-altitude-objects-2023/
  PHASED-PLAN.md
  timeline.yaml
  narratives.yaml
  seed-urls.yaml
  research/
    2026-MM-DD-verified-events.md
    2026-MM-DD-fourth-fifth-object-anomalies.md
    2026-MM-DD-ingestion-run.md
```

Method memos land under `dev/tell/docs/methods/results/`. No dashboard changes until Phase 6.

## 8. This PR

This PR contains only `PHASED-PLAN.md`. No timeline, narratives, seeds, or research dossiers are included. All of those are outputs of the phases defined above and ship in subsequent PRs.
