# Generalizability Plan

**Status:** Planning document. Written 2026-04-17.

**Purpose.** The praxis claims that the TELL architecture generalizes beyond NJ drones. A claim is not an argument. This document specifies the concrete case sequence, per-case evidence standard, and decision points that turn the generalizability claim into evidence committee members can evaluate.

## The problem this plan addresses

The NJ drones validation is strong within its domain. Six of eight TMP abstract claims are empirically validated. Three signal methods are stable across three corpus densities. Ground truth is hand-curated and canonical. That is good evidence for one case.

A reviewer from the human-factors tradition will ask one question: is this architecture a general-purpose instrument for information-environment sensemaking, or is it a post hoc fit to a single event? Without a second and a third case, the architecture-level claim in the proposal is defensible but unproven.

Two additional cases close the gap. A second retrospective in a different domain (the 2023 Chinese balloon) tells us the architecture is not overfit to NJ drones. A live case (H5N1) tells us the architecture is a working engineering system, not a retrospective lens. Together they substantiate the generalizability claim before the defense.

## Case sequence and timeline

### Case 1 (complete): NJ drones retrospective

- **Status:** Validated across three corpus densities (38, 96, 204 documents).
- **Domain:** UAP / unknown aerial phenomena.
- **Information-environment shape:** Institutional silence (38-day federal communication vacuum), narrative emergence faster than evidence (Iranian Mothership), echo-chamber amplification (SIG 1, 6x).
- **Time investment:** 4-5 months of pipeline development and corpus curation.
- **Evidence produced:** IVI peaked 17.0, NVD 1.20 on day of emergence, SIG 1/6x invariant across densities, entropy 86.5%, 6 of 8 claims validated.
- **Where it lives:** `dev/tell/data/nj-drones/`, `dev/tell/docs/abstract-claims.md`.

### Case 2 (planned, summer 2026): 2023 high-altitude balloon

- **Status:** Not yet started. Scoped here.
- **Domain:** State-attributed aerial surveillance incident.
- **Why this case.** The balloon case inverts almost every structural feature of NJ drones. Attribution was early, institutional response was fast, the dominant narrative (Chinese surveillance balloon) was confirmed rather than contested, and the forensic post-event record is richer. If IVI, NVD, and SIG are general signals about information-environment structure, they should produce a qualitatively different signature on this case. If they produce the same pattern they produced on NJ drones, the signals are NJ-drones-specific artifacts.
- **Expected signature (hypothesis).**
  - **IVI low throughout.** DoD statement on January 31 and public confirmation on February 2, 2023 close the controller loop early. Daily IVI should sit near 1-3, not 17.
  - **NVD at or below threshold for the primary narrative.** The Chinese-balloon narrative had evidence support from the beginning. NVD should not fire on the primary narrative, though it may fire on adjacent narratives (cargo contents, payload capability, flight path anomalies).
  - **SIG shows rising amplification over time, not instant echo-chamber.** Early coverage had multiple independent government sources. Later coverage derivative-cites those sources. Amplification ratio should grow from ~1 to ~3-5 over the event timeline, not start at 6x.
  - **Entropy lower than NJ drones.** A dominant explanation with evidence support means H1-H5 distributions collapse earlier. Premature closure is less of a concern; genuine closure is appropriate.
- **Corpus construction.**
  - Seed documents: Billings Gazette initial sighting (February 1), DoD statement (February 2), Biden shoot-down announcement (February 4), Pentagon post-event debrief (February 6), State Department follow-up through February 2023.
  - Target size: 150-250 documents across 30-45 sources. Matches NJ drones density bands.
  - Ground truth: dated canonical events in the same format as NJ drones timeline.
- **Hypothesis framework:** Different from NJ drones. Draft five hypotheses: H1 civilian weather balloon, H2 unintended drift of civilian research payload, H3 state civilian surveillance (ISR not targeted), H4 state military surveillance (targeted collection), H5 state provocation / deliberate signaling. JMill authors the canonical set.
- **Evidence standard.** Case 2 is a success if (a) the pipeline produces the expected inverted signature, (b) the three signal methods remain stable across two corpus densities (100 docs and 200 docs), and (c) at least one finding surfaces that was not obvious from surface-reading (analogous to the mass hysteria persistence finding on NJ drones).
- **Time investment estimate:** 4-6 weeks including corpus curation, hypothesis framework authoring, and report writing. The pipeline does not need substantive engineering changes to run this case.

### Case 3 (planned, ongoing from post-TMP through defense): H5N1 live surveillance

- **Status:** Not yet started. Scoped in detail at `dev/tell/docs/live-case-scope.md`.
- **Domain:** Emerging biosecurity / pandemic surveillance.
- **Why this case.** Live operation is the strongest evidence that the architecture is an engineering system and not a retrospective lens. H5N1 is the cleanest available live case (authoritative sources well-defined, discourse active, uncertainty genuine, horizon operationally meaningful). Biosecurity also connects directly to the praxis's Significance and Generalizability argument, which names pandemic surveillance as a primary application domain.
- **Expected signature (hypothesis).** Unknown. That is the point. The live case runs as discovery, not confirmation.
- **Evidence standard.** Case 3 is a success if (a) the pipeline runs continuously without human intervention for 90+ days, (b) the three signal methods remain interpretable to a reader who does not know H5N1 epidemiology, and (c) at least one signal movement corresponds to a known information-environment event (a CDC statement, a WHO DON, a published study) that a human reader can verify. Unsuccessful live operation is informative: it tells the committee where real-time ingestion breaks the architecture's assumptions.
- **Ethics and safety posture.** Detailed in the scope document. Noindex, auth-gated, collapsed source identities, persistent epistemic disclaimer, alert-suppression rule.

## What cross-case evidence looks like

The generalizability argument rests on four cross-case comparisons.

1. **Structural signature varies with information environment.** NJ drones (silent institutions, fast narratives): high IVI, firing NVD, low SIG independence. Balloon (responsive institutions, state-attributed narrative): low IVI, non-firing NVD on primary narrative, rising SIG amplification over time. If both cases produce the expected distinct signatures, the signals track environment structure rather than case-specific features.
2. **Signal stability across densities.** NJ drones showed the signals stable across 38 / 96 / 204 docs. Case 2 runs at two densities (100 / 200) and the live case runs continuously. Stability across densities within a case is necessary; stability of the stability property across cases is what generalizability actually means.
3. **Hypothesis-framework authoring produces discriminating H1-H5 distributions.** If the framework authoring works on NJ drones, on the balloon, and on H5N1, then the evaluation apparatus is portable. If one of the frameworks fails to discriminate (for example, all documents score 0.5 on all H5N1 hypotheses), the praxis's commitment to hand-authored hypothesis frameworks needs revisiting.
4. **Methods recover at least one non-obvious finding per case.** NJ drones: mass hysteria persistence (47-day unchallenged). Balloon: target hypothesis TBD. H5N1: whatever surfaces during live operation. A non-obvious finding per case is the weakest form of evidence that the pipeline is doing real analytical work, not just pattern-matching on curated corpora.

## Dependencies and risks

- **Corpus curation bias.** JMill hand-curates seeds for cases 1 and 2. The live case reduces this risk because adapter-pulled corpora are less curator-shaped. Documented in the live case scope.
- **Hypothesis-framework authoring risk.** Each case needs a hand-authored H1-H5 equivalent. That is real cognitive labor. Budget accordingly.
- **Live-case continuity risk.** If the pipeline goes down during the live case, the defense narrative weakens. Monitoring is a prerequisite, not an optional enhancement. Vercel deployment health + GitHub Actions ingestion schedule both need alerting.
- **Timing risk.** Case 2 targets summer 2026. If it slips past September, the defense schedule tightens. Case 3 runs continuously once started; starting late reduces evidence accumulation.

## Relationship to the TMP consortium

The CMU TMP Graduate Consortium on June 15-16, 2026 does not require cases 2 or 3 to be complete. The abstract commits to the NJ drones validation; the talk can honestly describe cases 2 and 3 as scoped and in progress. Running the balloon retrospective ahead of TMP is nice-to-have, not required. Running even a short live-case demo ahead of TMP would materially strengthen the "this is working engineering" pitch to any DARPA-adjacent or defense-adjacent audience members.

## Relationship to the proposal

This plan is the referent for three proposal sections.

- **Validation Strategy (Part I)** names the three cases and points here for detail.
- **What's Aspirational (Part II)** marks generalizability as aspirational until cases 2 and 3 produce results.
- **Risk Register (Part II)** cites this plan as the mitigation for the generalizability-undemonstrated risk.
