---
public_eligible: true
---

# Figures pending for CMU TMP 2026 talk

This directory holds the exported figures and the backup demo recording for the June 15-16 talk. Files referenced from `../slides-v02.md` and `../demo-script.md` land here. All formats below should ship in both SVG and PNG unless noted; SVG is preferred for slide layout, PNG is the export-of-record for archival and slide-deck portability.

## Inventory and target dates

| File | Sources for content | Target |
|---|---|---|
| `2026-nj-drones-timeline.svg` and `.png` | Dates in `../demo-script.md` section 2; emphasize the 38-day institutional vacuum visually | 2026-06-01 |
| `2026-three-information-failures.svg` and `.png` | Values in `dev/tell/docs/abstract-claims.md` (Iranian Mothership, Loose Nuke, Mass Hysteria; peak NVD, Source Independence score, contradicting-evidence lag) | 2026-06-01 |
| `2026-tell-architecture.svg` and `.png` | Reference `dev/tell/docs/architecture.md`. Data flow: Sources → Ingestion (Wayback + HTTP via trafilatura) → Corpus (Neon + Vercel Blob) → Hypothesis Scoring (H1-H5) → Signal Methods (IVI, NVD, SIG) → Evaluation (SQM) | 2026-06-01 |
| `2026-klein-to-signals-mapping.svg` and `.png` | Reference `dev/tell/docs/methods/framework-mapping.md`. Map Klein's six sensemaking activities (data, frame, anomaly detection, frame elaboration, frame questioning, frame reframing) to the three signal classes (IVI, NVD, SIG) | 2026-06-01 |
| `demo-recording.mp4` | 5-minute walkthrough of the IVI to NVD to SIG to Hypothesis-distribution sequence, recorded against the frozen production deploy at `https://tell-fyi.vercel.app`. Audio: JMill narrating in the same voice as `../demo-script.md` section 6. Must be recorded after the deploy freeze (above) so the recorded values match the live demo. | 2026-06-05 (after the 2026-06-01 deploy freeze; before the week-of-June-8 rehearsal that confirms the backup plays cleanly) |

## Production discipline

- The demo recording should be recorded only after the Vercel production deploy is pinned to a frozen Neon branch (target 2026-06-01), so the values shown in the recording match the values that will appear during the live demo.
- Figure aesthetic: dark background, light foreground, restrained color palette consistent with the editorial tokens documented under `dev/tell/web/`. No clip-art.
- File naming follows the `YYYY-<slug>` convention from `CLAUDE.md` File Conventions.

## Substrate-boundary discipline

The figures surface only the open substrate per `admin/milestones/substrate-specialization-framework.md`. No Omnissiah, OmniProject, Revenant, Corvus Labs, M2 Foundry, Endless Forge, or GEM imagery.
