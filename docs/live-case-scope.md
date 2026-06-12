# Live Case Scope: H5N1 Surveillance Pipeline

**Status:** Scoping document. Written 2026-04-17. Not yet implemented.

**Purpose.** This document specifies what the first live-case run of the TELL pipeline is, what it is not, and the engineering, ethical, and operational constraints that govern it. It is the source of truth for the live deployment and is referenced from `paper/drafts/praxis-proposal-v02.md` (Validation Strategy section) and `dev/tell/docs/generalizability-plan.md`.

## Why H5N1

H5N1 avian influenza is the cleanest live case available for the praxis to demonstrate real-time operation. Four properties make it tractable.

1. **Authoritative sources are well-defined.** CDC, WHO, USDA APHIS, state departments of public health, and the peer-reviewed epidemiology literature each occupy a clear position in STAMP's controller-vs-controlled-process partition. IVI has a crisp denominator.
2. **Discourse environment is active.** News reporting, Reddit, podcasts, and social media all produce observable volume on H5N1 developments, which means the IVI numerator is non-trivial and NVD has evidence to run against.
3. **Epidemiological uncertainty is genuine.** Questions about mammalian adaptation, human-to-human transmission risk, and case undercount are real and unsettled. Narratives are emerging and being revised in real time. That is exactly the regime the architecture claims to address.
4. **Horizon is operationally meaningful.** The pipeline can run against H5N1 continuously for six to twelve months without the event "resolving" in a way that shuts the corpus off. That is long enough to show pipeline behavior across multiple narrative cycles.

## What the live case is

A public, authenticated, research-mode dashboard that ingests H5N1-related documents daily, produces IVI, NVD, and SIG signals, and renders them in a dashboard matched to the NJ drones layout. The purpose is to generate evidence that the three novel signal methods are stable and interpretable on an environment the pipeline has not been tuned against.

## What the live case is not

The live case is explicitly **not**:

- A public-health alerting service. It does not tell anyone whether to be concerned about H5N1.
- An epidemiological model. It does not estimate case counts, R0, or any biological quantity.
- A journalism tool. It does not accuse any outlet of amplification or any speaker of narrative capture.
- A policy recommendation engine. It does not tell institutions what to say or when.

These disclaimers appear on the live dashboard in a persistent header and in the Methods page.

## Ingestion adapters

The live case uses the same adapter pattern as the NJ drones retrospective, extended with scheduled pulls. Adapters pull only from public, non-paywalled feeds.

| Adapter | Source | Classification | Cadence |
|---|---|---|---|
| `cdc_rss` | CDC H5N1 / avian influenza news and MMWR feeds | authoritative | daily |
| `who_rss` | WHO Disease Outbreak News (DON), WHO avian influenza updates | authoritative | daily |
| `usda_aphis` | USDA APHIS HPAI dairy cattle and poultry detection pages (scraped from published tables) | authoritative | daily |
| `pubmed_eutils` | PubMed E-utilities searches on H5N1 / HPAI H5 terms | authoritative | daily |
| `biorxiv_mcp` | bioRxiv MCP search on H5N1 / HPAI terms | authoritative | daily |
| `google_news_rss` | Google News RSS queries on "H5N1" and "bird flu" | discourse | every 6 hours |
| `reddit_json` | Reddit JSON listings on r/Virology, r/Coronavirus, r/Epidemiology H5N1 threads | discourse | daily |
| `gdelt_gkg` | GDELT GKG filtered on H5N1-relevant themes | discourse | daily |

State health department and county-level releases are ingested on a case-by-case basis when a specific jurisdiction becomes newsworthy.

All adapters respect `robots.txt` and source-specific terms of service. No authentication is bypassed. No paywalled content is scraped. Adapters that hit rate limits back off exponentially.

## Ethics and safety posture

Five constraints govern the live deployment.

1. **noindex.** The live dashboard serves `X-Robots-Tag: noindex, nofollow` and a matching `<meta>` tag. It is not indexed by search engines during the validation period.
2. **Auth-gated.** The live route is behind an authentication check during the validation period. Committee members and collaborators get access via email allowlist. The route is not publicly reachable by URL alone.
3. **Collapsed source identities.** On the live route, source-level identities are collapsed to (source_domain, source_kind) pairs. Individual reporter names, account handles, and podcast hosts are not displayed. The pipeline is evaluated on structural signals, not on person-level attribution. This is different from the NJ drones retrospective, where the case was historical and the public record already names the relevant speakers.
4. **Persistent epistemic disclaimer.** Every view of the live dashboard carries a banner stating that IVI, NVD, and SIG are research signals about the information environment, not epidemiological claims, and that the dashboard is not a public-health alert.
5. **Escalation rule.** If any signal on the live case fires in a way that could plausibly be misread as a public-health recommendation (for example, a capture-risk alert on a narrative that touches human-to-human transmission), the dashboard will suppress the alert UI and flag it to JMill for manual review before any onward communication. The rule will be implemented as a feature flag on the alert-rendering path, not as a human-in-the-loop prompt to prevent oversight bypass.

These constraints are specified for enforcement in code, not by convention, and are planned to live in the live-route layer with test coverage. None of them are implemented yet; this document is the design contract the live deployment must meet before any live run begins.

## Corpus growth estimates

Assumptions: ~20-50 documents per day on active days, ~5-15 on quiet days. Mean ~30/day. Over 90 days of live operation, corpus size reaches ~2,700 documents, comparable to five-to-ten NJ drones corpora concatenated.

## Cost bounds

LLM hypothesis scoring (H1-H5 equivalent for H5N1, which uses a different five-hypothesis framework specified in `data/h5n1/hypotheses.yaml` once created) runs batched overnight. At 30 documents/day and 5 hypotheses/document, with Claude Haiku 4.5 for classification (see project memory on current Claude model family), daily cost is ~$0.06-$0.15. Over 90 days, ~$6-$15 in scoring cost. Embeddings on Neon pgvector are negligible. This is not a cost-bound engineering problem.

## H5N1 hypothesis framework (to be authored)

The NJ drones H1-H5 framework does not transfer directly. A draft set of five hypotheses for H5N1 is:

- **H1.** Sporadic zoonotic spillover; no sustained mammalian adaptation.
- **H2.** Dairy-cattle reservoir with stable, undercounted human exposure but no human-to-human transmission.
- **H3.** Ongoing mammalian adaptation in non-human mammals with rising human-exposure risk; still no sustained human-to-human transmission.
- **H4.** Limited human-to-human transmission occurring undetected or underreported.
- **H5.** Sustained human-to-human transmission with pandemic potential.

JMill authors the canonical framework. Dates, thresholds, and narrative slugs come from JMill and from the hand-curated timeline. The pipeline does not produce them.

## What counts as success

Three outcomes, in decreasing order of informativeness.

1. **Signals track the structural shape of the H5N1 information environment.** IVI rises when institutional communication lags. NVD fires on narratives that outpace their evidence. SIG surfaces attribution chains when they are present and low amplification when coverage is genuinely multi-source. If this holds, the architecture has generalized to a second, fundamentally different domain.
2. **Signals behave in unexpected ways that have a diagnosable cause.** For example, IVI runs consistently low because CDC publishes daily and therefore the authoritative denominator never drops. That is a finding, not a failure; it teaches the limits of the signal and motivates refinement.
3. **Signals misfire in ways the pipeline cannot explain.** This is the disconfirmation case. If it happens, the architecture does not generalize as claimed and the praxis's generalizability argument requires revision. That outcome is accepted in advance.

## Out of scope for the live case

- State-level or county-level dashboards. The live route is national plus WHO-international only.
- Individual reporter or researcher amplification scores. Collapsed to (domain, kind) as above.
- Any feature that produces an alert outbound (email, SMS, webhook, RSS). The dashboard is read-only.
- Comparison across outbreak events (H5N1 vs monkeypox vs COVID). Post-defense, potentially. Not in the validation window.

## Sequencing

1. Author H5N1 hypotheses and narratives YAML. The current loaders hardcode the NJ drones layout (`data/hypotheses.yaml` at the root and `data/nj-drones/narratives.yaml`; see `dev/tell/python/signals_methods/src/signals_methods/constants.py`). The live-case work therefore has two sub-tasks that must land together: (a) parameterize both loaders so the pipeline resolves hypotheses and narratives by case name, and (b) author `data/h5n1/hypotheses.yaml` and `data/h5n1/narratives.yaml` against the new loader contract. Neither is done yet; (a) is the blocker for (b). Authoring is JMill's; the loader change is an implementation task.
2. Stand up adapters in a stub state; run each against a single day of output to confirm shape.
3. Backfill 30 days of history to populate the initial corpus and let SIG warm up.
4. Turn on daily scheduled ingestion (Vercel Cron + GitHub Actions for the Python pipeline).
5. Live dashboard goes auth-gated with the epistemic banner.
6. First demo to committee and collaborators after 30 days of continuous operation.

The live case does not need to be running before the CMU TMP consortium on June 15-16, 2026. It is a post-TMP deliverable that substantiates the praxis's generalizability claim before the defense.
