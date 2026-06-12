# Uncertainty formalisms

*Reference material. The praxis approximates these formalisms operationally; this document records the formal connections so future validation work can promote them to first-class metrics.*

**Status:** [REVIEW] Working reference document, 2026-05-05. Companion to `paper/sections/methodology.md` Step 6 and to the integration plan at `research/synthesis/2026-05-05-compendium-integration-plan.md`.

## Purpose

The praxis's empirical work uses three operational measures of uncertainty: per-document hypothesis distributions over H1 through H5 (`signals_analyze/hypothesis_scoring.py`), aggregated daily entropy (`signals_analyze/storage.py::aggregate_daily_distributions`), and threshold recalibration across corpus densities (NVD threshold compressed from 1.5 at 38 documents to 1.1 at 204 documents). Each of these has a formal substrate in the published literature. This document records the connections so future validation work knows where to look when promoting any of them to first-class metrics.

This is reference material, not implementation specification. None of these formalisms is currently implemented in TELL, and the integration plan is explicit that promotion to first-class metrics is future work.

## Conformal prediction (Angelopoulos and Bates, 2021)

Conformal prediction produces distribution-free, finite-sample coverage guarantees for predictive intervals. Given a calibration set and a target coverage level alpha, the conformal procedure returns a prediction set guaranteed to contain the true value with probability at least 1 minus alpha, regardless of the underlying distribution.

The natural connection to the praxis: the H1 through H5 distribution and the entropy floor that emerges from it are exactly the kind of structured-uncertainty object conformal prediction is designed to validate. Two specific connections:

- The aggregated daily distribution can be read as the prediction set: the probabilities for each hypothesis at each time window. Conformal coverage would ask whether the true hypothesis (where ground truth exists, as in the NJ drones validation case) falls within the high-probability mass at the claimed confidence level.

- The premature-closure-resistance metric (mean entropy 86.5% of maximum across 26 days, floor 57.4% on the 96-doc corpus) is operationally what conformal coverage is measuring formally: the system's capacity to maintain valid prediction sets even when individual hypotheses become more or less probable.

Implementation hooks (future): `signals_analyze/storage.py` already aggregates daily distributions. A conformal validation pass would compute the empirical coverage rate against a held-out validation set with ground-truth hypothesis labels, calibrate thresholds against the desired coverage level, and report conformal coverage as a fifth SQM metric alongside the four existing ones (coverage, alignment, responsiveness, premature-closure resistance).

## Wasserstein distributionally-robust optimization (Mohajerin Esfahani and Kuhn, 2018)

Wasserstein DRO replaces the empirical distribution with the worst-case distribution within an epsilon-ball (in Wasserstein metric) of the empirical. The result is a robustness guarantee: the optimal decision under Wasserstein DRO is robust against any distribution that could plausibly have generated the observed data, up to the epsilon-radius of the ball.

The natural connection to the praxis: threshold recalibration across corpus densities is a Wasserstein DRO problem stated implicitly. The NVD threshold compressed from 1.5 at 38 documents to 1.1 at 204 documents because the empirical distribution of NVD values shifts as the corpus density grows. The praxis recalibrates by inspection. Wasserstein DRO would recalibrate by computing the worst-case threshold within a Wasserstein ball whose radius is calibrated to the corpus-size-dependent variance of NVD.

Implementation hooks (future): the threshold-recalibration logic in `eval.py::compute_capture_risk` currently uses inspection-based thresholds in `constants.py`. A Wasserstein DRO pass would compute thresholds robustly against worst-case Wasserstein perturbations of the empirical NVD distribution, with the epsilon-radius chosen as a function of corpus size. This would automate what the praxis currently does manually and would produce thresholds with explicit robustness guarantees.

## Markov-category-enriched composable uncertainty (Furter, Huang, and Zardini, 2025)

Furter, Huang, and Zardini (Applied Category Theory 2025; arXiv:2503.17274) lifted Censi's monotone co-design framework from Boolean to probabilistic uncertainty via Markov-category enrichment. The result is a categorical framework in which uncertainty over typed compositions is composable: combining an uncertain component with another uncertain component produces a composite whose uncertainty is computable from the components' uncertainties under explicit Markov-category laws.

The natural connection to the praxis: the prescriptive advisory layer composes signal state, controller jurisdiction, available actions, and narrative relationship into role-differentiated recommendations. Each of these inputs carries uncertainty (signals are noisy; controller authority can be ambiguous; narrative classifications are probabilistic). A Markov-category-enriched co-design framework would express the advisory's uncertainty as a composition of the input uncertainties under explicit composition laws.

Implementation hooks (future): this is a research-level connection rather than an immediate engineering hook. The Markov-category framework would not change the prescriptive layer's behavior at TMP 2026, but it would give the praxis a formal vocabulary in which to claim that the advisory's uncertainty is composable rather than aggregated post-hoc. This is the strongest form of the substrate-vs-specialization framework's claim that the praxis substrate is open and the commercial specializations live on top: the substrate is a composable-uncertainty framework; the specializations choose specific component implementations.

## Connection map

| Operational praxis measure | Formal substrate | Promotion path |
|---|---|---|
| H1-H5 entropy floor (premature-closure resistance) | Conformal prediction (Angelopoulos and Bates, 2021) | Add conformal coverage as fifth SQM metric in `signals_methods/eval.py` |
| Threshold recalibration across corpus densities | Wasserstein DRO (Mohajerin Esfahani and Kuhn, 2018) | Replace inspection-based thresholds in `constants.py` with Wasserstein-robust thresholds computed from corpus statistics |
| Compositional advisory uncertainty | Markov-category-enriched co-design (Furter, Huang, and Zardini, 2025) | Research-level connection; not an immediate engineering hook |

## What is not implemented

The praxis does not currently implement any of these formalisms as first-class metrics. The connections documented here are reference material, not specifications. Three reasons for the deferral:

1. The empirical work for TMP 2026 stands on the existing operational measures. Promoting any of these formalisms to first-class metrics would expand scope without strengthening the abstract's claims.
2. Conformal coverage and Wasserstein DRO require a held-out validation set with ground-truth labels, which the NJ drones case provides at the timeline level but not at the document-hypothesis level. Building that calibration set is non-trivial.
3. The Markov-category framework is a research direction, not a deployment direction. Pursuing it would be a separate output (a CIRP Annals or IEEE T-RO paper) rather than a TELL pipeline change.

## When to revisit

Three triggers would justify promoting one or more of these formalisms to first-class metrics:

- A second domain instantiation completes (manufacturing composition validation, self-driving labs, or H5N1) and the cross-corpus threshold behavior becomes harder to defend by inspection. Wasserstein DRO would be the answer.
- Committee review surfaces a request for stronger uncertainty quantification than the current entropy-floor approach provides. Conformal coverage would be the answer.
- A joint paper opportunity with Zardini's group emerges. The Markov-category framework would be the entry point.

## References

- Angelopoulos, A. N., & Bates, S. (2021). A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification. arXiv:2107.07511.
- Furter, A., Huang, Y., & Zardini, G. (2025). Composable Uncertainty in Symmetric Monoidal Categories for Design Problems. *Applied Category Theory 2025*. arXiv:2503.17274.
- Mohajerin Esfahani, P., & Kuhn, D. (2018). Data-driven Distributionally Robust Optimization Using the Wasserstein Metric: Performance Guarantees and Tractable Reformulations. *Mathematical Programming*, 171(1-2), 115-166.
