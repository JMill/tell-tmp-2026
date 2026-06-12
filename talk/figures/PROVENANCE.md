---
public_eligible: true
---

# Figure Provenance — CMU TMP 2026 Talk

Every figure renders from committed data. Extraction queries ran read-only against the production Neon branch on 2026-06-10; each JSON file under `data/` embeds the exact SQL that produced it.

Each figure exists in two variants from the same script and data. The dense editorial set in this directory is for reading distance: the repo, the printed one-pager, anyone studying the charts. The projector set in `stage/` is what goes into the Keynote: type and marks scaled 1.5×, long captions shortened, and the timeline reduced to the six events that carry the visual story (the speaker narrates the rest). Numbers are identical across variants. Rebuild both with:

```
uv run --with matplotlib --with pyyaml --no-project \
    python engagements/2026-tmp-cmu/talk/figures/build/build_figures.py
FIG_SCALE=1.5 uv run --with matplotlib --with pyyaml --no-project \
    python engagements/2026-tmp-cmu/talk/figures/build/build_figures.py
```

Corpus: `nj-drones-2026-04-09` analysis build (105 scored documents from 49 source domains; 203 documents accumulated across the three NJ drones builds). The claim ledger at `dev/tell/docs/abstract-claims.md` is the cross-reference for every number.

| Figure | Data source | Key numbers and their verification |
|---|---|---|
| fig1-timeline | `dev/tell/data/nj-drones/timeline.yaml` (hand-audited ground truth, version 0.2.0-draft) | Event dates and titles read directly from the YAML. The 38-day silence spans Dec 21, 2024 to Jan 27, 2025. |
| fig2-ivi | `data/ivi_7d.json` (`signal_ivi`, 7-day windows) | Peak 17.0 on Dec 24 (17 discourse, 0 authoritative). Matches claim 2 in the ledger. |
| fig3-nvd | `data/nvd_3d.json` (`signal_nvd`, 3-day windows, 2026-04-09 build) | Iranian Mothership 1.20 on Dec 11-12; drones-legit 1.53 on Dec 18. Matches claim 3. |
| fig4-hypotheses | `data/hypotheses.json` (`hypothesis_distributions`, 2026-04-09 build) | 29 scored days; mean entropy 86.6% of the 2.322-bit maximum; Jan 10 entropy 2.24. Days after Jan 28, 2025 (later retrospectives) are omitted from the axis; the 65.6% entropy floor falls on one of those omitted retrospective days. Matches claim 7 summary row. |
| fig5-independence | `data/independence.json` (`signal_independence`, 2026-04-09 build) | Iranian Mothership: 6 documents, 1 independent source, 6.0× amplification. Drones-legit: 105 documents, 31 independent, 3.4×. Matches claim 4. |
| fig6-stability | Builds 1-2 from the ledger (38-doc and 96-doc results recorded in `abstract-claims.md`); build 3 verified against `signal_nvd` and `signal_independence` | NVD compression 2.00 → 1.50 → 1.20; independence score 1 and 6× amplification invariant; capture-risk alert fires on Dec 11 in every build. The 38-doc and 96-doc signal rows were overwritten by later recomputes, so those two points cite the ledger, not live tables. |
| fig7-sqm | Live run of `signals compute eval --topic nj-drones --corpus nj-drones-2026-04-09` on 2026-06-10 | Lags 0h (Mothership), 0h (Loose Nuke), 1,128h (Mass Hysteria). Capture-risk Dec 11 (2.40) and Dec 12 (2.33). Alignment 53 of 55 windows (96.4%). Closure resistance mean 86.6%, floor 65.6%. |

## Divergences from the April ledger

Two ledger values are stale relative to the current eval code and were superseded by the live 2026-06-10 run:

1. **Alignment windows.** The ledger records 47 windows, 2 misaligned (95.7%). The live run produces 55 windows, 2 misaligned (96.4%). The eval code evolved after the ledger entry (PR 33 cleanup). The talk uses the live numbers.
2. **Peak-entropy day.** Earlier corpus builds put peak entropy on Dec 11; in the 2026-04-09 build the maximum (2.238 bits) falls on Jan 10, 2025. The talk's hypothesis figure annotates Jan 10.

One framing decision, made by JMill on 2026-06-10: the submitted abstract says "204-document corpus." The database holds 203 NJ drones documents across builds, and the analysis build that produced the signal values scored 105. Slides say "200+ documents accumulated across three builds, 105 scored in the analysis build." Speaker notes carry the exact accounting.

The ledger refresh (alignment windows, peak-entropy day, corpus accounting) is follow-up work, tracked in the PR description for this talk kit.
