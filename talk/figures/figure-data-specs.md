---
public_eligible: true
---

# Figure data specifications

Precise data for all four pending figures. Each spec contains every value needed to go straight to design in any vector tool. Reference `README.md` for format requirements (SVG + PNG, dark background, editorial aesthetic).

---

## Figure 1: NJ drones timeline

**File:** `2026-nj-drones-timeline.svg` / `.png`
**Slide reference:** slide 3
**Layout:** Horizontal timeline, left to right, dark background. Key dates as labeled points. The 38-day institutional vacuum (Dec 21 to Jan 27) should be visually prominent (shaded region, different background, or bracketed annotation).

| Date | Event | Visual treatment |
|------|-------|-----------------|
| 2024-11-18 | First sightings in Morris County, NJ | Start point |
| 2024-12-10 | Rep. Van Drew claims "Iranian drone mothership" on Fox News | Red accent marker |
| 2024-12-11 | Pentagon denies Iranian Mothership claim (same day as Van Drew); NVD peaks at 1.20; composite capture-risk fires (2.40) | Red accent, annotation |
| 2024-12-12 | Composite capture-risk fires again (2.33) | Subtle continuation |
| 2024-12-19 | FAA issues 22 Temporary Flight Restrictions with deadly-force authorization | Notable marker |
| 2024-12-21 | Start of 38-day institutional silence | Start of shaded region |
| 2024-12-24 | IVI peaks at 17.0 (17 discourse docs, 0 authoritative in 7-day window) | Peak annotation inside shaded region |
| 2025-01-27 | End of institutional silence | End of shaded region |
| 2025-01-28 | Trump White House statement: "not the enemy," authorized research and hobbyists | End point |

**Duration labels:** "38-day institutional vacuum" spanning Dec 21 to Jan 27. "14-week episode" spanning the full Nov 18 to Jan 28 range.

---

## Figure 2: Three information failures comparison

**File:** `2026-three-information-failures.svg` / `.png`
**Slide reference:** slide 4
**Layout:** Three-column comparison grid. Each column is one narrative. Rows are metrics. Dark background. Values should be the visual focus.

| Metric | Iranian Mothership | Mass Hysteria | Loose Nuke |
|--------|-------------------|---------------|------------|
| **Origin** | Single congressman (Van Drew on Fox News, Dec 10) | Institutional default (misidentification thesis) | Single podcast (unverified claim about Picatinny Arsenal) |
| **Spread** | 6 outlets, 6 domains | Unchallenged institutional narrative | Migrated to mainstream media |
| **Peak NVD** | 1.20 (Dec 11) | 0.20 | 0.50 |
| **Source Independence score** | 1 | 1 | 3 |
| **Amplification ratio** | 6x | 4x | 0.7x |
| **Contradicting-evidence lag** | 0 hours (Pentagon denial same day) | 1,128 hours (47 days unchallenged) | 0 hours (post-fix) |

**Color coding:** Iranian Mothership = red/urgent (fast capture, fast detection). Mass Hysteria = amber/structural (slow capture, slow detection). Loose Nuke = muted (supporting example).

**Key insight annotation:** "Same dashboard, two different failure modes: rapid echo-chamber capture vs. structural institutional resistance to contradiction."

---

## Figure 3: TELL architecture diagram

**File:** `2026-tell-architecture.svg` / `.png`
**Slide reference:** slide 6
**Layout:** Left-to-right data flow. Five stages. Dark background. Clean boxes with connecting arrows.

```
SOURCES          INGESTION           CORPUS              ANALYSIS            EVALUATION
─────────       ──────────          ──────               ────────            ──────────
Gov (.gov)  ──► Wayback CDX    ──► Neon Postgres   ──► H1-H5 Hypothesis ──► SQM Metrics
News        ──► Direct HTTP        + pgvector           Scoring               • Contradicting-
Aviation    ──► (trafilatura)      Vercel Blob      ──► IVI                     evidence lag
Academic    ──►                                     ──► NVD                   • Composite
Social/     ──►                                     ──► SIG                     capture risk
 Podcast                                                                     • Evidence-
                                                                               narrative
                                                                               alignment
                                                                             • Premature
                                                                               closure
                                                                               resistance
                                                        │
                                                        ▼
                                                    DASHBOARD
                                                    Next.js / Vercel
                                                    (Server Components
                                                     + Drizzle + Visx)
```

**Label detail:**
- Sources box: "49+ sources, 5 categories, 204 documents"
- Ingestion box: "Python offline" (small subtitle)
- Corpus box: "Neon + Blob" (small subtitle)
- Analysis box: "Three novel signal methods" (small subtitle)
- Evaluation box: "Four sensemaking quality metrics" (small subtitle)
- Dashboard box: "tell-fyi.vercel.app" with QR code if space permits

**Color:** Single accent color for signal methods (IVI, NVD, SIG). Everything else in neutral tones.

---

## Figure 4: Klein-to-signals mapping

**File:** `2026-klein-to-signals-mapping.svg` / `.png`
**Slide reference:** slide 5b
**Layout:** Two-column mapping. Left column: Klein's six sensemaking activities. Right column: signal classes and STAMP failure modes. Connecting lines show which activities map to which signals.

| Klein Activity | Signal Class | STAMP Failure Mode | Mapping logic |
|---------------|-------------|-------------------|---------------|
| **Elaborating** | (Not directly instrumented) | — | Elaborating builds richer pictures from evidence; supported by corpus density, not a specific signal |
| **Questioning** | NVD | Process model divergence | NVD asks: "Is there enough evidence to justify how fast this claim is spreading?" |
| **Connecting** | SIG | Sensor degradation | SIG asks: "Do these two sources actually trace to independent observations?" |
| **Comparing** | Entropy floor | Premature model commitment | Entropy metric asks: "Has the system closed on one explanation before evidence warrants it?" |
| **Framing** | H1-H5 hypothesis distribution | — | The five-hypothesis framework maintains multiple frames simultaneously |
| **Re-Framing** | IVI + Composite alert | Inadequate control action | IVI detects when the institutional frame is not responding to reality; composite fires when multiple signals converge |

**Visual treatment:** Colored connecting lines from Klein activities to signal classes. Klein activities on the left in a vertical stack. Signal classes on the right in a vertical stack. STAMP failure modes as small annotations on each connecting line.

**Key annotation:** "Klein's activities enter as design requirements, not post-hoc framing. Each signal was designed to support a specific sensemaking activity."
