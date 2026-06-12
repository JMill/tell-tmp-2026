# Domain Instantiation Guide

*How to apply sensemaking-by-design to a new domain.*

This guide describes the engineering process for applying the praxis methodology to any domain where multi-human + machine systems must detect anomalies under uncertainty. The process was developed through the TELL pipeline's information-environment instantiation and validated against the November 2024 to January 2025 New Jersey aerial phenomena incident.

The methodology is domain-agnostic. The instantiation is domain-specific. This document describes the seven steps that produce a domain-specific instantiation from the general methodology.

## Prerequisites

The methodology applies to domains with these structural properties:

1. **Multiple competing explanations circulate simultaneously.** The system must maintain uncertainty across alternatives rather than collapsing to a single answer.
2. **Institutional actors have authority to act but imperfect information.** Controllers in the STAMP sense exist and can issue control actions, but their process models may diverge from reality.
3. **Representational mismatch is the failure mode.** The system can fail not because sensors are weak but because the model of "normal" is the wrong shape for the reality being observed.
4. **Sensemaking quality matters more than prediction accuracy.** The goal is maintaining appropriate uncertainty and enabling timely frame-switching, not predicting the correct outcome.

If a domain lacks these properties (e.g., a well-characterized process with a single correct answer and no institutional complexity), standard anomaly detection methods are sufficient and this methodology adds unnecessary complexity.

## Step 1: Model the domain as a STAMP control structure

Identify the control hierarchy:

- **Controllers:** Who has authority to act? What decisions do they make? In information environments, these are institutions (FAA, DHS, Congress). In manufacturing, these are design engineers, process engineers, quality inspectors, and regulatory bodies.
- **Controlled process:** What is the process being controlled? In information environments, this is public discourse and belief formation. In manufacturing, this is the production process.
- **Actuators:** What actions can controllers take? In information environments, these are public statements, investigations, and policy changes. In manufacturing, these are process parameter changes, tool selections, and supplier substitutions.
- **Sensors:** What provides feedback to controllers? In information environments, these are media monitoring, public comment, and FOIA. In manufacturing, these are quality measurements, test results, and field failure reports.
- **Feedback loops:** How does information flow from the process back to the controller? What is the latency? Where can feedback be corrupted or lost?

Write this as a `controllers.yaml` file following the pattern in `data/nj-drones/controllers.yaml`. Each controller needs: slug, label, role, stamp_function, jurisdiction, available_actions, information_needs, and narrative relationships.

## Step 2: Define the domain's hypothesis space

Define 3-7 competing hypotheses that represent the space of explanations for anomalies in this domain. These are the equivalent of the CU26 H1-H5 framework.

Requirements:
- Hypotheses must be **collectively exhaustive** (every possible anomaly falls under at least one)
- Hypotheses should be **mutually informative** (scoring a document against one hypothesis provides information about the others)
- Hypotheses should use **independent probability scoring** (a single observation can support multiple hypotheses simultaneously; do not force a probability distribution that sums to 1)

Write this as a `hypotheses.yaml` file.

## Step 3: Define the domain's narratives or frames

Identify the competing explanations, narratives, or interpretive frames that circulate among practitioners and stakeholders in this domain. These are the equivalent of `narratives.yaml`.

Each narrative needs:
- A stable slug for machine reference
- Keywords or matching criteria for associating observations with the narrative
- A mapping to one or more hypotheses
- An originating source (who introduced this frame?)
- An evidence weight (strong, moderate, weak, rumor)

The number of narratives depends on the domain. Information environments may have 5-10 competing narratives. Manufacturing quality analysis may have 3-5 competing failure modes. Medical diagnosis may have the full differential.

## Step 4: Map signal types to the domain's observables

The three signal methods (IVI, NVD, SIG) measure general patterns of sensemaking failure. Each domain must define what plays the role of these signals.

### IVI: Response gap

IVI measures the gap between demand for authoritative response and supply of it. Define:
- **Demand sources:** What generates questions, discourse, or requirements that need institutional response? (Information: news, social media. Manufacturing: design change requests, customer specs. Medical: patient symptoms, test results.)
- **Supply sources:** What provides authoritative answers? (Information: government, academic. Manufacturing: validated process data, material certifications. Medical: diagnostic tests, specialist consultations.)
- **The ratio** of demand to supply, smoothed over a rolling window, is the domain's IVI.

### NVD: Model-evidence divergence

NVD measures when a narrative or model spreads faster than evidence supports. Define:
- **Narrative velocity:** How fast is a particular explanation spreading? (Information: document count per narrative per window. Manufacturing: how many teams are adopting a particular process assumption. Medical: how quickly a working diagnosis propagates across the care team.)
- **Evidence velocity:** How fast is supporting evidence accumulating? (Information: documents scoring above threshold on the narrative's hypothesis. Manufacturing: test results confirming the process assumption. Medical: diagnostic tests confirming the working diagnosis.)
- **The ratio** of narrative velocity to evidence velocity is the domain's NVD.

### SIG: Corroboration independence

SIG measures whether apparent corroboration traces to independent sources or is echo amplification. Define:
- **Sources:** What are the information sources in this domain? (Information: news outlets, government agencies. Manufacturing: suppliers, test laboratories, inspection stations. Medical: diagnostic instruments, specialist opinions, reference laboratories.)
- **Attribution:** How do you trace whether source B's claim derives from source A? (Information: title-level attribution heuristics. Manufacturing: supplier sub-tier analysis. Medical: whether two lab results used the same instrument or reference standard.)
- **Independence score:** Count of truly independent sources confirming a claim.

### Thresholds

Set initial thresholds from domain expertise or calibration data:
- IVI threshold: ratio above which the response gap is concerning
- NVD threshold: ratio above which a narrative is outpacing evidence
- SIG independence threshold: score below which corroboration is illusory
- Composite risk: when all three converge on the same narrative/frame

Expect to recalibrate thresholds as the corpus grows. The NJ drones experience showed NVD thresholds compress with denser corpora (1.5 at 38 docs, 1.1 at 204 docs).

## Step 5: Define controllers and their available actions

For each controller identified in Step 1, define:
- What signal types are relevant to their role (information_needs)
- What actions they can take in response to signal conditions (available_actions)
- Their relationship to each narrative (originator, responder, monitor, amplifier)

Write prescriptive advisory templates in domain-appropriate language. The templates map signal conditions to recommended actions:

| Signal Condition | STAMP Failure Mode | Template Pattern |
|---|---|---|
| IVI > threshold | Inadequate control action | "[Controller] should [available_action] to address [demand/supply gap]" |
| NVD > threshold on narrative X | Process model divergence | "[Controller] should [release evidence / validate assumption] for [narrative]. Current model-evidence ratio: [NVD]x" |
| SIG independence <= threshold on narrative X | Sensor degradation | "[Narrative] lacks independent corroboration. [N] apparent sources trace to [origin]. Do not treat volume as verification." |
| Composite risk | Unsafe control action preconditions | "ALERT: [narrative] shows [vacuum + divergence + echo] conditions. Prioritize evidence-based response." |

## Step 6: Validate against a retrospective case with known ground truth

Select a historical case where the outcome is known and construct:
- A **ground-truth timeline** of events (hand-curated, not LLM-generated)
- A **corpus** of documents, observations, or records from the case
- **Hypothesis scores** for each observation against the hypothesis space

Run the signal methods and prescriptive logic against this corpus. Verify:
- Do the signals fire at the right times?
- Do the advisories reach the right controllers?
- Does the composite risk alert fire before the failure event?
- Does the system maintain appropriate uncertainty (entropy stays above floor)?

Document discrepancies. Recalibrate thresholds. The first retrospective validation is a calibration exercise, not a test. The second case (different scenario, same domain) is the real validation.

The validation judge in this loop must be the threshold-bound checker, not another LLM. The growing literature on LLM-as-judge failure modes (Zheng et al. 2023 "Judging LLM-as-a-Judge with MT-Bench"; the position-bias and self-consistency work that followed in 2024-2025) shows that LLMs systematically misjudge engineering correctness when not augmented with executable verification. The praxis's prescriptive layer is template-based for exactly this reason: the recommendation must be auditable from the signal state, and an LLM-generated advisory makes that audit chain ambiguous. Apply the same discipline at validation time. Signal thresholds and STAMP failure-mode classification provide the ground truth against which advisories are checked, not LLM consensus on whether the advisory "looks right."

## Step 7: Characterize gaps and boundary conditions

After validation, document:
- Where did the methodology transfer cleanly from the reference domain?
- Where did it require domain-specific adaptation?
- What domain properties made it more or less applicable?
- What are the boundary conditions for this domain instantiation?

This documentation is the contribution. The methodology claims domain-agnosticism; the validation evidence shows where that claim holds and where it requires qualification.

## Candidate cross-domain instantiations

Beyond information environments (validated through TELL) and manufacturing composition (designed through the Omnissiah collaboration), three additional domains are candidate instantiations. They are listed here as starting points for future instantiation work; only the first is currently prioritized.

### Self-driving laboratories (priority)

Chemistry and materials-science self-driving laboratories are the closest published analog of the diagnostic-and-prescriptive pipeline TELL embodies: a hypothesis space (candidate molecules or processes), automated evaluation (instrument output scored against hypotheses), structured uncertainty over alternatives (Bayesian or evolutionary search maintained over the candidate set), and prescriptive next-experiment selection. The canonical published systems are Coley et al. 2019 (*Science*), Burger et al. 2020 (*Nature*), MacLeod et al. 2020 (*Science Advances*), Roch et al. 2018 (*Science Robotics*), and the Materials Acceleration Platform (Aspuru-Guzik and Persson 2018). Public datasets and published benchmarks make this the strongest immediate candidate for a third validated instantiation. JMill review on 2026-05-05 prioritized this candidate over genetic-circuit design and economic-statecraft.

### Genetic-circuit design

Cello (Nielsen et al. 2016, *Science*) is the strongest biology-to-engineering analog: an EDA stack for living circuits, with SBOL (Galdzicki et al. 2014, *Nature Biotechnology*) playing the role of an SBOM-for-living-circuits. The biology domain has the typed-composition substrate the Endless Forge framing identifies as the architectural prerequisite. Domain-expertise gap is moderate; this would benefit from explicit collaboration with a synthetic-biology group.

### Economic statecraft

Farrell and Newman's "Weaponized Interdependence" (*International Security* 44(1), 2019; Brookings volume 2021) framework treats sanctions, export controls, and chokepoint exploitation as instruments composed against an adversary's network position. The compositional pattern is structurally identical to the engineering case (typed primitives, composition rules, search problem, human-judgment step), but validation here would be qualitative-historical rather than computational. Strong fit for a defense-school engagement narrative; less actionable for the QE timeline.

## Reference instantiation: Information environments (TELL)

The complete reference implementation lives at `dev/tell/`. Key files:

| Step | File |
|---|---|
| Controllers | `data/nj-drones/controllers.yaml` |
| Hypotheses | H1-H5 defined in `signals_core/models.py` |
| Narratives | `data/nj-drones/narratives.yaml` |
| Signal methods | `signals_methods/ivi.py`, `nvd.py`, `independence.py` |
| Prescriptive logic | `signals_methods/prescribe.py` |
| Evaluation | `signals_methods/eval.py` |
| Ground truth | `data/nj-drones/timeline.yaml` |
| Validation results | `docs/methods/ivi.md`, `nvd.md`, `independence.md`, `sqm.md` |
