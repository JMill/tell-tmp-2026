# Sensemaking Quality, Not Prediction

## Three measures for detecting narrative capture in real time

**Jonathan Miller** · Doctor of Engineering, Penn State College of Engineering · May 2026
TELL pipeline overview · `tell-fyi.vercel.app/brief` · v0.1 working draft

---

## Abstract

When public discourse outruns institutional response during ambiguous, high-uncertainty events, unevidenced narratives capture the resulting vacuum. The 2024 New Jersey aerial phenomena incident produced a measurable case: more than five thousand FBI tips, four federal agencies declaring "nothing anomalous," a congressional claim of an Iranian drone mothership, a podcast-originated loose-nuclear-weapon theory, and a 269 percent surge in laser strikes against commercial aircraft. TELL is an open-source intelligence pipeline that asks an upstream question. Rather than predicting what an event was, it evaluates whether the information environment was supporting human sensemaking while the answer was unknown. Three novel measures target distinct failure modes. Klein's sensemaking framework and Leveson's STAMP control-structure modeling enter as design requirements rather than post-hoc rhetoric. Retrospective analysis of a 204-document corpus surfaces the structural conditions of narrative capture and produces results stable across three corpus densities.

---

## The Three Measures

**Information Vacuum Index (IVI).** A rolling-window ratio between the count of public discourse documents and the count of authoritative documents from federal agencies, congressional offices, and primary investigators. Above one means more public talk than institutional response. Above ten means a structural vacuum.

**Narrative Velocity Divergence (NVD).** A per-narrative ratio between the rate at which a named narrative spreads and the rate at which evidence supporting it accumulates. Above one means the narrative is outpacing its evidence base. Computed for each of eight named narratives across the corpus.

**Source Independence Graph (SIG).** A topology measure that traces every document carrying a narrative back to its attributable origin source, then computes the number of independent sources versus the count of amplifying outlets. A score of one with a high amplification ratio is the structural signature of an echo chamber, not corroboration.

These three plug into four Sensemaking Quality Metrics: contradicting-evidence lag, composite narrative-capture risk, evidence-narrative alignment, and premature-closure resistance.

## Headline Findings

| Measure | Result | Date |
|---|---|---|
| IVI peak | **17.0** (17 discourse documents, 0 authoritative responses) | 2024-12-24 |
| Iranian Mothership NVD | **1.20** (narrative outpacing evidence on day of emergence) | 2024-12-11 |
| Iranian Mothership SIG | **score 1, 6× amplification** (six domains, one origin source) | invariant |
| Mass-hysteria contradicting-evidence lag | **1,128 hours** (47 days unchallenged) | 2024-12-16 |
| Composite capture-risk alert | fires on Iranian Mothership | 2024-12-11, 12 |
| Mean entropy across hypotheses (H1–H5) | **86.5%** of theoretical maximum (no hypothesis zeros out) | 26 days |
| Evidence-narrative alignment | **95.7%** of windows | 47 windows |

The Iranian Mothership result is invariant across corpus sizes of 38, 96, and 204 documents. The 1,128-hour lag on the institutional mass-hysteria framing is not a pipeline failure. It is a measurement of which framings institutional silence protects.

## Validation Status

Eight abstract claims, scored against committed code, persisted data, and reproducible test runs:

| Claim | Status |
|---|---|
| Multi-source ingestion (gov, news, aviation, academic, social) | **validated** |
| Information Vacuum Index | **validated** |
| Narrative Velocity Divergence | **validated** |
| Source Independence Graph | **validated** |
| Klein and Leveson as design requirements | partial |
| Surfaces contradicting evidence within hours | partial (2 of 3 narratives same-day) |
| Maintains structured uncertainty across hypotheses | **validated** |
| Flags conditions conducive to narrative capture | **validated** |

Six validated, two partial. Stability of the three signal methods confirmed across three corpus builds.

## Generalization

The New Jersey case is the validation corpus, not the point. The architecture generalizes to ambiguous high-uncertainty events with the same structural shape: biosecurity incidents where early reports are unclear and institutional response is deliberately slow, emerging-technology governance where public discourse outpaces regulatory understanding, contested-attribution cyber incidents, and critical-infrastructure failures with competing pre-root-cause explanations.

## Resources

- **Live dashboard.** `tell-fyi.vercel.app`
- **Reproducible claim ledger.** `dev/tell/docs/abstract-claims.md`
- **Architecture mapping (Klein + Leveson).** `dev/tell/docs/methods/framework-mapping.md`
- **Methods documentation.** `dev/tell/docs/methods/` (`ivi.md`, `nvd.md`, `independence.md`, `sqm.md`)
- **Citation.** Miller, TELL pipeline, Penn State D.Eng. praxis, 2026.
