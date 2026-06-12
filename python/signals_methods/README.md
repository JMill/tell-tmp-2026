# signals_methods

Four novel weak-signal detection methods for sensemaking under uncertainty. Introduced as part of JMill's Doctor of Engineering praxis at Penn State (*Sensemaking by Design: An Engineering Architecture for Anomaly Detection in Systems That Can't Afford to Be Wrong*) and validated empirically against the November 2024 to January 2025 New Jersey aerial phenomena incident.

The package is case-study-agnostic. The NJ-drones data that drove development is one instantiation; the 2023 high-altitude balloon retrospective and the H5N1 live-surveillance case study both use the same four methods against different narrative and timeline YAMLs.

## Methods

| Method | Module | What it measures |
|---|---|---|
| **Information Vacuum Index (IVI)** | `signals_methods.ivi` | Structural imbalance between discourse activity and authoritative activity within a rolling window. High IVI marks moments when the public discourse is talking faster than institutions are providing evidence. |
| **Narrative Velocity Divergence (NVD)** | `signals_methods.nvd` | Per-narrative ratio of narrative velocity (how fast a claim accretes coverage) to evidence velocity (how fast supporting or contradicting evidence lands). NVD >> 1 marks narratives outpacing their evidence. |
| **Source Independence Graph (SIG)** | `signals_methods.independence` | Per-narrative independence score and amplification ratio computed from a citation graph over the corpus. Low independence plus high amplification is the structural signature of echo-chamber propagation. |
| **Sensemaking Quality Metrics (SQM)** | `signals_methods.eval` | Four evaluation metrics connecting the three signals back to a ground-truth timeline: contradicting evidence lag, composite capture-risk alerts, evidence-narrative alignment, and premature closure resistance. |

Each method is implemented as a pure function over plain-Python records. The methods do not depend on any database, LLM, or storage layer. Persisting results to Postgres or Vercel Blob is handled by the CLI and storage modules that sit on top.

## Install

This package is part of the TELL monorepo and distributed via a uv workspace. The Python-only dependencies are `signals-core` (data models, utility primitives), PyYAML, and `psycopg[binary]` (only used by the storage layer; the computation core does not import it).

From within `dev/tell/`:

```bash
uv sync
uv run signals compute ivi --help
```

To consume `signals_methods` from outside the TELL workspace, clone the repository and install from source:

```bash
pip install -e dev/tell/python/signals_methods
pip install -e dev/tell/python/signals_core
```

A standalone PyPI release is not published yet. When it is, the canonical name will be `signals-methods`.

## Usage

### Against the built-in NJ-drones case study

```bash
uv run signals compute ivi --topic nj-drones --corpus nj-drones-2026-04-08 --window-days 7
uv run signals compute nvd --topic nj-drones --corpus nj-drones-2026-04-08
uv run signals compute independence --topic nj-drones --corpus nj-drones-2026-04-08
uv run signals compute eval --topic nj-drones --corpus nj-drones-2026-04-08
```

### Against an arbitrary case study

The eval command accepts `--narratives <path/to/narratives.yaml>` and `--timeline <path/to/timeline.yaml>` so the full SQM suite runs against any case study whose YAMLs match the documented schemas:

```bash
uv run signals compute eval \
  --corpus 2023-balloons-v1 --topic 2023-balloons \
  --narratives data/2023-balloons/narratives.yaml \
  --timeline data/2023-balloons/timeline.yaml
```

### Programmatic use

```python
from signals_methods.constants import load_narrative_defs
from signals_methods.eval import load_timeline_from_yaml
from signals_methods.nvd import compute_nvd
from signals_methods.independence import compute_independence

narratives = load_narrative_defs("data/my-case/narratives.yaml")
timeline = load_timeline_from_yaml("data/my-case/timeline.yaml")

nvd_points = compute_nvd(docs, hypothesis_scores, narrative_defs=narratives)
sig_rows = compute_independence(docs, narrative_defs=narratives)
```

Every compute function accepts a `narrative_defs` parameter for explicit injection and falls back to the package-level `NARRATIVE_DEFS` constant only when one is not supplied. Importing `signals_methods` from outside `dev/tell/` yields an empty `NARRATIVE_DEFS`, so explicit injection is the recommended pattern for any new case study.

## Data schemas

**narratives.yaml**

```yaml
narratives:
  - slug: iranian-mothership
    label: "Iranian mothership off the Jersey coast"
    hypothesis_id: H4                    # the CU26 H1-H5 bucket
    keywords: ["iranian", "mothership"]
    originating_source: "Rep. Jeff Van Drew (R-NJ), 2024-12-11"
```

**timeline.yaml**

```yaml
events:
  - id: vandrew-mothership-claim-2024-12-11
    date: 2024-12-11                     # ISO 8601 date
    title: "Rep. Van Drew claims Iranian mothership on Fox News"
    category: narrative-claim            # narrative-claim | observation | resolution
    narratives: [iranian-mothership]
    evidence_weight: weak                # strong | moderate | weak | rumor
```

See `dev/tell/data/nj-drones/` for a complete working example.

## Empirical validation

All four methods have been computed across three corpus densities of the NJ-drones case (38, 96, and 204 documents). Headline results from the 204-doc corpus:

- Iranian Mothership contradicting-evidence lag: **0 hours** (stable across corpus sizes)
- IVI peak: **17.00 on Dec 24** with the 7-day window; vacuum window correctly identified
- NVD: Iranian Mothership 1.20 on Dec 11-12; drones-legit 1.53 on Dec 18 (threshold recalibrated from 1.5 to 1.1 for denser corpora)
- SIG: Iranian Mothership independence 1, amplification 6×; drones-legit 31 / 3.4×
- Composite capture-risk: Dec 11 (risk 2.40) and Dec 12 (risk 2.33) alerts fire
- Evidence-narrative alignment: 47 windows, 2 misaligned (95.7%)
- Premature closure resistance: mean 86.5%, floor 57.4%, 26 days

Full numbers and interpretation live in the CMU TMP 2026 paper draft at `paper/drafts/praxis-proposal-v02.md` and in `dev/tell/docs/abstract-claims.md`.

## Citing

Pre-publication citation (to be updated on first PyPI or Zenodo release):

```bibtex
@software{miller_signals_methods_2026,
  author       = {Miller, Jonathan},
  title        = {signals\_methods: Weak-signal detection methods for sensemaking under uncertainty},
  year         = {2026},
  url          = {https://github.com/JMill/praxis-deng/tree/main/dev/tell/python/signals_methods},
  note         = {Part of the Doctor of Engineering praxis at Penn State}
}
```

A machine-readable `CITATION.cff` is included at the package root.

## License

TBD. The package ships without a SPDX-listed license as of 2026-04. Contact JMill before redistribution.

## Related packages in this monorepo

- `signals_core` — shared pydantic models and utility primitives (env, db, dates, display, HTML extraction). Required dependency.
- `signals_ingest` — Wayback and Direct HTTP ingestion adapters on top of `signals_core.extract` and `signals_ingest.adapters.base`.
- `signals_analyze` — LLM-driven hypothesis scoring (Claude tool calls for H1-H5) feeding NVD and SIG.
- `vercel_blob_client` — reverse-engineered Python REST client for Vercel Blob (storage dependency for signals_ingest).
