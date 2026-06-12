# Cross-Case Signal Hypotheses

**Compiled:** 2026-04-19
**Purpose:** Pre-registered predictions about how the four TELL signal methods should behave on the February 2023 high-altitude objects corpus, grounded in the NJ drones validated numbers. Authored before Phase 5 runs so that confirmation and disconfirmation can be evaluated against commitments made in advance.

This memo is a predictive instrument. It commits to specific numerical bands and directional claims for each signal and each narrative, so that the Phase 5 results memos can read "confirmed", "disconfirmed", or "refined" against a target rather than against impressions formed after seeing the data. The post-Phase-5 cross-case synthesis memo at `docs/methods/results/` will answer these predictions.

## 1. Why this memo exists

The TELL methods were developed against one case. A single validation run cannot distinguish a general-purpose sensemaking instrument from an instrument overfit to the conditions of NJ drones. A second case tests whether the instruments generalize. The more the February 2023 case diverges structurally from NJ drones, the stronger the generalizability test.

The epistemic risk of running Phase 5 without a prior commitment is familiar: after-the-fact rationalization turns any data shape into "consistent with theory." Pre-registration converts that risk into an explicit scorecard. The praxis argues that sensemaking tools should be evaluable. An unevaluable tool is a narrative, not an instrument.

## 2. The two cases, side by side

| Dimension | NJ drones (Nov 2024 - Jan 2025) | High-altitude objects (Feb 2023) |
|-----------|----------------------------------|-----------------------------------|
| Triggering event | Private observations of lights above residential areas, rapidly coalescing via social media | Military radar detection of a known state actor's airborne platform |
| Duration of intense discourse | 10+ weeks | 2 weeks for the core cluster; 5-month long tail to attribution |
| Dominant-narrative share at peak | Low (5+ live narratives at any moment) | Moderate (PRC surveillance was dominant by Feb 3) |
| Physical recovery | None | One recovered (balloon off Surfside Beach); three unrecovered (Yukon, Alaska, Lake Huron) |
| Authoritative attribution cadence | Very slow (weeks of ambiguity before FBI statements) | Staged (Feb 2 PRC attribution; Feb 16 pico-balloon; Jun 29 SIGINT confirmation) |
| Narrative originator topology | Diffuse (social, podcasters, one congressional statement) | Concentrated (DoD and White House drove the dominant narrative from day one) |
| Physical kinematics of objects | Plausible commercial drones, a few edge cases | Slow, high-altitude, low-signature; three of five were genuinely anomalous |
| Institutional admission of uncertainty | Rare | On-record (SecDef Austin: miss-and-re-engage at Lake Huron; Kirby: "we have not seen anything like this") |
| Resolution state | Partially closed (most cases benign) | Closed for one object, stuck open for three |

Five structural features cluster the cases. Both involve ambiguous aerial phenomena within US airspace, institutional uncertainty under public scrutiny, multi-actor narrative contention, asymmetric information flows between government and citizens, and hypothesis persistence after official closure claims. Five structural features separate them. NJ drones was civilian-originated; 2023 was state-adversary-originated. NJ drones lacked authoritative forensic evidence; 2023 produced definitive forensic evidence for one of five events. NJ drones ran for weeks at low intensity; 2023 ran at crisis intensity for two weeks. NJ drones had no successful intercepts; 2023 had four. NJ drones never resolved; 2023 resolved partially.

A method that worked only on NJ drones would be suspect. A method that worked only on 2023 would be equally suspect. Signal behavior that holds across both is evidence of generalizability. Signal behavior that diverges systematically with structural features is evidence that the methods are sensitive to the right things.

## 3. NJ drones empirical anchors

These are the validated numbers the 2023 case is being compared against. Source: `docs/abstract-claims.md` at the 204-document corpus density, last recomputed 2026-04-09.

- **IVI peak: 17.00** on the 7-day window ending 2024-12-24. Dec 16-25 covers the top 10 IVI values. Peak condition: 17 discourse documents, 0 authoritative documents in the window.
- **NVD (3-day window, threshold 1.1):** `iranian-mothership` 1.20 on Dec 11-12; `drones-legit` 1.53 on Dec 18. These are the two narratives that exceeded threshold.
- **SIG:** `iranian-mothership` independence score 1, amplification 6×. `drones-legit` independence score 31, amplification 3.4×. The ratio between these two narratives (31:1) captures the echo-versus-corroboration distinction the signal was built to surface.
- **Capture-risk alerts:** Dec 11 (risk 2.40) and Dec 12 (risk 2.33), both firing on `iranian-mothership`. All three signals converged on the same narrative on the same day.
- **Alignment:** 47 windows analyzed, 2 misaligned (95.7% alignment).
- **Closure resistance:** mean 86.5%, floor 57.4%, 26 days analyzed.
- **Contradicting-evidence lag:** `iranian-mothership` 0 hours. `loose-nuke` 0 hours. `mass-hysteria` 1,128 hours.

The `iranian-mothership` triple (high NVD + low SIG + high IVI + fast contradicting evidence) is the signature of narrative capture that gets corrected quickly. The `mass-hysteria` 1,128-hour lag is the signature of a narrative that survives in the information environment long after contradicting evidence appears. These two shapes constitute the diagnostic language the 2023 case will be read through.

## 4. Per-signal predictions for February 2023

### 4.1 Information Vacuum Index (IVI)

The NJ drones IVI peak coincided with a period when no federal agency had issued an official explanation and the holiday calendar suppressed authoritative output. The 2023 case structurally differs: authoritative output was intense and continuous from February 2 onward. The Pentagon, White House, FAA, NORAD, and Canadian Department of National Defence all briefed publicly during the two-week core cluster. If IVI captures what it is meant to capture, its peak should therefore appear at a different moment and at a different magnitude.

**Prediction 4.1.1 (peak location).** IVI peak falls on the 7-day window ending between Feb 10 and Feb 14, 2023. These three days contain the anomalous-objects intercepts (Feb 10 Alaska, Feb 11 Yukon, Feb 12 Lake Huron). They were also the period of highest discourse volume with the sparsest pre-authoritative interpretation. The DoD, NORAD, and White House were briefing daily, but briefing output lagged shoot-down events by 18 to 36 hours, creating a narrow vacuum window that discourse filled first.

**Prediction 4.1.2 (peak magnitude).** IVI peak value between 6.0 and 10.0 on a 7-day window. This is significantly lower than the NJ drones peak of 17.0. The 2023 authoritative output is continuous where NJ drones was sparse, so the discourse-to-authoritative ratio should run lower. A peak above 10.0 would indicate the corpus is missing authoritative documents on the intercept days and would require an ingestion audit. A peak below 4.0 would indicate IVI is under-responsive to the genuinely vacuum-like hours between Feb 11 engagement and Feb 13 Kirby briefing.

**Prediction 4.1.3 (shape).** IVI traces a sharp rise from Feb 10 to Feb 14 and a steep decline after Feb 16 as the hobbyist-pico-balloon explanation reduces discourse volume and the Biden national-security statement on Feb 16 adds authoritative weight. The 204-day long tail from Feb 17 to Jun 29 should show low and stable IVI.

**Prediction 4.1.4 (3-day window peak).** On the 3-day window that the composite capture-risk path uses (`EVAL_IVI_WINDOW_DAYS = 3`), IVI peaks between Feb 11 and Feb 14 at a value between 4.5 and 8.0. The 3-day window is not a scaled-down version of the 7-day window: on NJ drones, the Dec 11 capture-risk alert fired at 3-day IVI 5.5 while the 7-day IVI on that same day was below 5.0 (see `sqm.md` § Temporal alignment). The 3-day window concentrates short vacuum moments where a 7-day window dilutes them across surrounding days. The 2023 Feb 11-14 sequence is a short, concentrated vacuum, so the 3-day peak should sit in a range that overlaps the 5.0 capture-risk threshold rather than clearing it by a wide margin. If the 3-day peak exceeds 8.0 the corpus is likely missing Feb 11-14 authoritative documents and needs an ingestion audit. If it falls below 4.0 the 5.0 threshold is miscalibrated for this case and the composite will under-fire.

**What this tests.** IVI should detect a genuine vacuum window even when authoritative sources are prolific but lagged. If IVI fails to elevate during Feb 10-14 or elevates somewhere outside the cluster, the method is probably detecting "low authoritative count" rather than "discourse-authoritative gap". This is the non-trivial generalizability test.

### 4.2 Narrative Velocity Divergence (NVD)

The NJ drones NVD results showed a narrative (`iranian-mothership`) that spread fast and collected no evidence (velocity 1.20 at threshold 1.1) and a narrative (`drones-legit`) that spread fast and collected plausible but inconclusive evidence (velocity 1.53). The 2023 corpus contains eight narratives with radically different evidence trajectories.

**Prediction 4.2.1 (hobbyist-pico-balloon).** NVD value for `hobbyist-pico-balloon` peaks on the 3-day window ending Feb 17 or Feb 18, 2023, at a value between 2.0 and 4.0. The Aviation Week article surfaced the Northern Illinois Bottlecap Balloon Brigade on Feb 16. NIBBB posted the K9YO-15 track data shortly thereafter. Social and news narrative velocity should exceed evidence velocity by a wide margin because the community itself is small and its corroborating infrastructure (WSPR spots, amateur radio logs) produces non-standard "evidence" that the corpus may not capture.

**Prediction 4.2.2 (misidentification-threshold).** NVD value for `misidentification-threshold` peaks on the 3-day window ending Feb 13 or Feb 14, 2023, at a value between 1.5 and 3.0. NORAD and White House briefings introduced this narrative explicitly on Feb 12 (VanHerck: adjusting filter thresholds) and Feb 13 (Kirby: may be benign recreational/research balloons). The narrative explains the anomaly after the fact rather than before, so narrative velocity should outpace evidence velocity for several days.

**Prediction 4.2.3 (prc-surveillance).** NVD value for `prc-surveillance` stays below 1.5 throughout the entire window. This narrative accumulated evidence continuously from Feb 2 (DoD attribution, radar tracks) through Jun 29 (FBI SIGINT confirmation). Evidence velocity should roughly match or slightly lead narrative velocity because institutional attribution preceded civilian amplification. A high NVD on `prc-surveillance` would indicate either a corpus gap in authoritative documents or that the narrative's keyword definitions are incorrectly tuned.

**Prediction 4.2.4 (classified-us-tech, adversary-black-tech).** Both narratives carry NVD values below 1.1 except in isolated 3-day windows on Feb 12, Feb 17, and any date near the Feb 14 Montana airspace-closure reporting. These are speculation-heavy narratives originating in online commentary; low baseline velocity with isolated spikes around anomaly-rich days is the expected shape.

**Prediction 4.2.5 (uap-unknown, official-recreation-research).** `uap-unknown` carries stable moderate NVD (1.0 to 1.5) across the entire window because the residual-unknown category absorbs commentary from multiple actors. `official-recreation-research` shows a single NVD spike on Feb 14-15 (the Kirby framing day) followed by a collapse as evidence fails to materialize. The collapse itself is a diagnostic: the narrative was offered as attribution, then abandoned when the recreational-balloon community did not claim the anomalous objects.

**Prediction 4.2.6 (prc-civilian-weather).** NVD value for `prc-civilian-weather` peaks on the 3-day window ending Feb 4 or Feb 5, 2023, at a value between 1.3 and 2.2. The PRC Ministry of Foreign Affairs asserted the civilian-airship claim on Feb 3 and Wang Wenbin reiterated it Feb 13-15. Narrative velocity should exceed evidence velocity because no corroborating evidence accumulates in the corpus; US institutional response contradicts the claim almost immediately (NYT Feb 8 SIGINT payload reporting; Feb 9 H.Res.104 passed 419-0; Feb 10 BIS Entity List addition). NVD should decay below 1.0 after Feb 10 as the PRC claim is displaced from Western-tier-1 discourse. A second minor spike on Feb 13-15 (the Wang reiteration) is possible but should stay below 1.5.

**What this tests.** NVD should distinguish four failure shapes: narratives where velocity and evidence accumulate in step (`prc-surveillance`); narratives offered as attribution that fail to recruit evidence (`official-recreation-research`); narratives where velocity outpaces evidence because the evidence lives outside the corpus (`hobbyist-pico-balloon`); and narratives asserted by a named state actor and quickly contradicted by competing authoritative sources (`prc-civilian-weather`). Four distinct failure modes, four distinct NVD signatures. If the method returns one signature for more than one of these, it is not measuring what it claims to measure.

### 4.3 Source Independence Graph (SIG)

The NJ drones SIG produced a 31:1 independence-score ratio between `drones-legit` and `iranian-mothership`. The 2023 case offers a richer differentiation opportunity because multiple narratives have distinct originator topologies.

**Prediction 4.3.1 (prc-surveillance).** Independence score between 10 and 25. Originator topology includes DoD, NORAD, NAV, CSIS, Canada Department of National Defence, Reuters, AP, NYT, WaPo, and CNA. The narrative was asserted independently by multiple authoritative institutions rather than amplified from a single origin. Amplification ratio should sit between 2.0 and 3.4, strictly below the NJ drones `drones-legit` ratio of 3.4×. The upper bound is pinned below 3.4 rather than overlapping it because this narrative is structurally less echoable than NJ drones' `drones-legit`: most of its documents are primary institutional assertions rather than secondary reporting of a single originator, so the ratio of amplifiers to origins should be smaller.

**Prediction 4.3.2 (official-recreation-research).** Independence score between 1 and 3, amplification ratio between 5.0 and 10.0. Kirby's Feb 14 White House briefing is the single origin. Every subsequent instance of this narrative in the corpus cites or paraphrases that briefing. This is the structural twin of `iranian-mothership`: one origin, many amplifiers, narrative collapse when evidence fails to materialize.

**Prediction 4.3.3 (hobbyist-pico-balloon).** Independence score between 3 and 6. Aviation Week's Feb 16 reporting is one origin; NIBBB's own statements are a second; tier-1 news replay is mostly amplification. The amplification ratio should be moderate (2.0 to 4.0) because the narrative has a small but genuine independent-source base.

**Prediction 4.3.4 (misidentification-threshold).** Independence score between 2 and 4. NORAD and White House are origins; news reporting is amplification. This is the narrative that exists to explain an anomaly after-the-fact; its SIG profile should show low independent corroboration and high amplification within the institutional-comms echo chamber.

**Prediction 4.3.5 (classified-us-tech, adversary-black-tech, uap-unknown).** Independence scores of 1 or 2. These are speculation narratives with minimal originator structure and thin evidence bases. Amplification ratios vary widely because they are mostly transient commentary rather than sustained reporting.

**Prediction 4.3.6 (prc-civilian-weather).** Independence score between 1 and 3, amplification ratio between 4.0 and 8.0. The PRC Ministry of Foreign Affairs is the single authoritative origin, with Wang Wenbin reiterations counting as the same source. PRC state media (Xinhua, CGTN, if present in the corpus) would amplify; Western tier-1 news typically reports the claim with frame-skeptical framing, which contributes to amplification rather than independent corroboration. Structurally analogous to `official-recreation-research` but from a different institutional actor. An independence score above 5 would indicate the corpus is treating frame-skeptical Western reporting as independent endorsement, which is a known SIG tuning pitfall worth surfacing.

**What this tests.** SIG should distinguish broadly corroborated claims (multiple independent authoritative origins) from single-origin institutional claims (state-actor assertions with narrow corroboration, regardless of whether the state actor is US or PRC) from echo chambers (one origin, many amplifiers within one discourse community) from small-community claims (few origins, moderate amplification) from pure speculation (one or zero origins, variable amplification). The 31:1 NJ drones ratio should reappear as a comparable discriminator in the 2023 data, with the highest independence narrative (`prc-surveillance`) and the lowest of the single-origin narratives (`official-recreation-research` or `prc-civilian-weather`) at a ratio of at least 5:1 even at the reduced expected magnitude.

### 4.4 Sensemaking Quality Metrics (SQM)

SQM computes four metrics. Each gets its own prediction set.

**Prediction 4.4.1 (contradicting-evidence lag for official-recreation-research).** The Kirby Feb 14 framing is a narrative-claim event. Contradicting evidence appears within 48 hours as the recreational-balloon community fails to claim the anomalous objects and the Canadian Forces Chief of Defence Staff declines to endorse the framing on Feb 15. Expected lag: 24 to 72 hours. Strong contradictory finding if the lag is observed, because this is a narrative the White House itself produced and then abandoned.

**Prediction 4.4.2 (contradicting-evidence lag for prc-civilian-weather).** The PRC Ministry of Foreign Affairs Feb 3 statement is a narrative-claim event. Contradicting evidence appears within 48 hours in the Pentagon Feb 4 briefing. Expected lag: 18 to 48 hours. Very short.

**Prediction 4.4.3 (contradicting-evidence lag for hobbyist-pico-balloon).** The Aviation Week Feb 16 reporting is a narrative-claim event. Contradicting evidence never fully accumulates within the window because no authoritative body confirms or denies the specific K9YO-15 identification of the Yukon object. Expected lag: either very long (> 500 hours) or null (no contradicting evidence in the corpus). The null result is itself a diagnostic that the corpus is missing the critical NTSB, RCAF, or FAA document that would adjudicate.

**Prediction 4.4.4 (capture-risk alerts).** All three signals (IVI high, NVD high, SIG low) converge on either `hobbyist-pico-balloon` on Feb 17-18 or `official-recreation-research` on Feb 14-15. The NJ drones case fired 2 capture-risk alerts over 10+ weeks. The 2023 case should fire 1 to 3 alerts concentrated in the Feb 10-17 window. A zero-alert result would indicate either that the signals under-responded or that the 2023 case simply did not contain the specific narrative-capture pattern.

**Prediction 4.4.5 (alignment).** Window-level alignment rate between 85% and 95%. The NJ drones rate of 95.7% reflects a corpus where evidence usually tracked loudness. The 2023 corpus includes two narratives (`official-recreation-research` and `hobbyist-pico-balloon`) that were loud without being best-supported; the misalignment count should therefore be slightly higher. Expected misaligned windows: 2 to 6 out of approximately 40 windows. This follows directly from the 85%-95% band (5%-15% misalignment × ~40 windows); the two bounds are two views of the same prediction, not independent bands.

**Prediction 4.4.6 (closure resistance).** Mean closure resistance between 70% and 85%, floor between 40% and 60%. The 2023 case has more authoritative attribution than NJ drones, so the hypothesis distribution should be narrower and the entropy floor lower. A floor below 40% would indicate that the corpus collapsed onto `prc-surveillance` prematurely, which given the resolved-for-one, unresolved-for-three empirical status is actually inappropriate. The `fourth-fifth-object-anomalies` dossier argues that the three unrecovered objects legitimately sustain H4 and H5 probability mass months after the shootdowns. If the SQM closure-resistance floor drops below 40%, the measure is overweighting the one resolved case and underweighting the three unresolved cases.

**What this tests.** SQM is a composite instrument. Each metric tests a different failure mode. Alignment tests whether the corpus as a whole tracks evidence. Closure resistance tests whether hypothesis distributions stay open under pressure. Contradicting-evidence lag tests the speed of the reality-correction cycle. Capture-risk tests the rare but critical three-way signal convergence. A strong 2023 run has at least three of the four metrics land within predicted bands.

## 5. What would falsify which claim

Reading Phase 5 results requires knowing in advance what would force theory revision. For each method:

- **IVI falsified.** Peak falls outside Feb 10-16 or peak magnitude exceeds 15. Either condition indicates IVI is driven by corpus imbalance rather than genuine vacuum structure.
- **NVD falsified.** `prc-surveillance` NVD exceeds 2.0 on any window, or `official-recreation-research` NVD fails to collapse after Feb 16. Either condition indicates NVD is insensitive to evidence-accumulation trajectories.
- **SIG falsified.** `prc-surveillance` independence score is below 5, or `official-recreation-research` independence score exceeds 5. Either condition indicates SIG cannot distinguish multi-origin corroboration from single-origin amplification on this corpus.
- **SQM falsified.** SQM is a composite of four metrics; each carries its own falsification rule, and the method as a whole is falsified when two or more of the four land outside band.
  - **Capture-risk.** Zero alerts fire anywhere in the Feb 10-17 window, OR more than 5 alerts fire across the full window. Under-response indicates insensitivity to genuine narrative capture; over-response indicates the thresholds are too loose for a denser corpus.
  - **Alignment.** Rate exceeds 98% (the corpus is too sanitized to contain narrative misalignment, which the structural features of the 2023 case rule out), OR rate falls below 75% (the measure is over-detecting misalignment in a corpus whose dominant narrative was genuinely well-supported).
  - **Contradicting-evidence lag.** `official-recreation-research` lag exceeds 200 hours (the measure cannot detect that the White House itself quietly abandoned the framing within days), OR `prc-civilian-weather` lag exceeds 200 hours (the measure cannot detect that a state-actor claim was contradicted by competing authoritative sources within 48 hours). Either condition indicates the method is insensitive to fast-contradiction dynamics on named-actor claims.
  - **Closure resistance.** Mean falls below 60% (hypothesis distributions collapse uniformly across the corpus), OR floor drops below 30% (the corpus collapses prematurely onto `prc-surveillance` despite three of five objects remaining unresolved). Either condition indicates the measure is overweighting the one resolved case and misreading the sustained ambiguity documented in `dev/tell/data/high-altitude-objects-2023/research/2026-04-19-fourth-fifth-object-anomalies.md`.

Disconfirmation for any one signal is a refinement opportunity, not a method kill. Disconfirmation for two or more signals on the same case is evidence of overfitting to NJ drones and forces re-examination of the definitions. Falsification of SQM itself requires two of its four sub-metrics to land outside band, because any single SQM metric failing in isolation is diagnostic information about that metric rather than a verdict on the composite instrument.

## 6. Where the 2023 case tests generalizability hardest

Three features of the 2023 case stress-test the methods in ways NJ drones could not.

**Test 1: rapid authoritative production.** NJ drones had sparse authoritative output. The pipeline's ability to detect a vacuum when authoritative output is sparse is plausibly trivial. The 2023 case has rapid authoritative output that still lags events. If IVI catches the Feb 10-14 vacuum, the method is detecting relative-response-time structure, not absolute authoritative volume.

**Test 2: dominant-narrative asymmetry.** NJ drones had five live narratives competing roughly evenly. The 2023 case has one dominant narrative (`prc-surveillance`) with evidence so strong that the other narratives exist mostly in the Feb 10-17 cluster. If NVD and SIG return interpretable numbers for low-volume narratives in the shadow of a dominant competitor, the methods are robust to narrative skew. If they collapse or return nonsense, they require dominant-narrative-normalization extensions.

**Test 3: partial closure.** NJ drones never closed. The 2023 case closed for one object (the Chinese balloon, Jun 29 SIGINT confirmation) and did not close for the other three. If SQM closure-resistance tracks this asymmetry (moderate-to-high ratio overall because three cases stay open), the metric is sensitive to narrative-specific resolution. If SQM closure-resistance collapses because the resolved case dominates, the metric is measuring corpus-level distribution rather than narrative-level persistence.

These three tests together make the 2023 run genuinely informative. The signals either generalize or they fail. No middle ground.

## 7. Reading the Phase 5 numbers against this memo

The post-Phase-5 results memo should include, per metric, a three-column table: "predicted range", "observed value", "fit". "Fit" is one of:

- **confirmed** — observed within predicted range
- **refined** — observed near predicted range with directionally correct signal; specific numerical adjustment required
- **disconfirmed** — observed outside predicted range with signal direction wrong; theory revision required

Claims that move from pre-registered predicted bands to observed values without explicit fit assessment are not legitimate confirmation. The praxis paper's cross-case generalization argument depends on this being done rigorously.

## 8. Open calibration items before Phase 5

Three items that cannot be resolved in this memo but that need operator attention before reading Phase 5 results:

1. **Evidence threshold.** The current default is 0.35 on the H1-H5 scoring scale. The 2023 narrative keyword definitions are tighter than NJ drones (for example `prc-surveillance` uses `["china", "prc", "spy balloon", "surveillance balloon", "pla"]` which matches only explicitly China-tagged documents). The threshold may need recalibration if too many `prc-surveillance` documents fall below 0.35 because the keyword match is satisfied but the narrative-specific evidence (SIGINT payload, trajectory analysis) is not scored as H4.

2. **NVD threshold.** NJ drones recalibrated from 1.5 to 1.1 at the 204-document density. The 2023 corpus is expected to be 90 to 110 documents, sitting between the 96-doc and 204-doc NJ drones densities. The threshold is fixed at 1.1 for Phase 5 and will not be adjusted based on observed Phase 5 values. This is deliberate: allowing a post-hoc relaxation to 1.0 if no points exceed 1.1 would convert a disconfirming run (nothing clears threshold) into an apparent confirmation at a lower bar, which is the canonical failure mode pre-registration exists to prevent. If the Phase 5 observations include zero narrative-day points above 1.1, the result is reported as observed and entered into the per-metric NVD falsification assessment in Section 5. Any later threshold change is a cross-case methodological decision that requires a third independent corpus, not a one-case post-hoc adjustment.

3. **Capture-risk triple-convergence threshold.** The existing thresholds (IVI ≥ 5.0, NVD ≥ 1.1, independence ≤ 2.0) were tuned on NJ drones. The IVI threshold must be read on the 3-day window because the composite capture-risk evaluator uses `EVAL_IVI_WINDOW_DAYS = 3`, not the 7-day window used for the standalone IVI series. The 2023 3-day IVI peak prediction (Prediction 4.1.4) is 4.5 to 8.0. The threshold of 5.0 sits inside that band, mirroring the NJ drones calibration where the Dec 11 alert fired at 3-day IVI 5.5 against the same threshold. This is the intended design: a threshold tuned just below the expected peak so the composite fires on genuine vacuum moments and holds its fire on the long tail. The 7-day IVI peak prediction (6.0 to 10.0) is for narrative discussion of the vacuum's overall magnitude, not for calibration of the composite threshold. The independence ≤ 2.0 threshold cleanly captures the lower bulk of the `official-recreation-research` predicted range (1 to 3) and the lower bulk of `prc-civilian-weather` (1 to 3), which is the intended behavior: both are single-origin narratives that the threshold was built to flag. It does *not* capture most of the `misidentification-threshold` predicted range (2 to 4), which is also intentional: the `misidentification-threshold` narrative has moderate independence by design (NORAD plus White House are distinct origins), so a capture-risk alert on that narrative would misfire. The threshold's asymmetric behavior across these three narratives is a feature, not a calibration miss. No pre-Phase-5 threshold revision.

## 9. What a publishable finding looks like

If this memo's predictions are mostly confirmed, the praxis paper's generalizability argument strengthens from "validated on one case" to "validated on two cases with shared structural features and divergent empirical mechanics." That is the standard cross-case-study argument in the field.

If a specific prediction is disconfirmed and the method reveals a failure mode on this corpus (for example, SIG cannot distinguish between `hobbyist-pico-balloon` and `misidentification-threshold` because the corpus lacks the NIBBB primary sources that differentiate them), the paper gains something more valuable than confirmation: a specific generalization limit documented under controlled conditions. The paper should treat this as a strength, not a weakness, and explicitly name the boundary condition.

The worst-case outcome is not disconfirmation. It is a run that produces numbers so close to the NJ drones results that generalization cannot be distinguished from coincidence. To guard against this, the predictions above deliberately include several that differ from the NJ drones numbers (IVI peak 6.0-10.0 vs. NJ's 17.0; capture-risk alerts 1-3 vs. NJ's 2; alignment 85-95% vs. NJ's 95.7%). A case with genuinely different structure should produce genuinely different numbers that still behave according to theory. Non-trivial similarity is the target, not coincidental similarity.
