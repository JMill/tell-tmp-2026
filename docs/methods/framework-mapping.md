# Framework Mapping: Klein and Leveson in the Pipeline Architecture

**Status:** Written 2026-04-08. Maps the abstract's Claim 5 ("The architecture embeds sensemaking theory (Klein, 2007) and systems-theoretic accident modeling (Leveson, 2012) as design requirements") to specific code and design decisions.

This document is the evidence for Claim 5. It demonstrates that Klein and Leveson are not decorative citations but structural choices that shaped the pipeline's data model, method design, and evaluation framework.

## Klein's sensemaking framework in the pipeline

Klein (2007) identifies six cognitive activities that characterize expert sensemaking: Elaborating, Questioning, Connecting, Comparing, Framing, and Re-Framing. Each appears in the pipeline as a design requirement that constrains how the system processes information.

### 1. Elaborating: building up a mental model from data

Klein's Elaborating is the act of filling in gaps, seeking more detail, constructing a richer picture from incomplete evidence.

**In the pipeline:** The hypothesis scoring module (`signals_analyze/hypothesis_scoring.py`) instantiates Elaborating computationally. For each document, the system produces independent probability estimates across H1-H5, building up a progressively richer picture of how the evidence distributes across competing explanations. The daily hypothesis distributions (`hypothesis_distributions` table) are the pipeline's evolving mental model, updated with every new piece of evidence.

The design decision that makes this Elaborating rather than classification: hypothesis scores are independent probabilities, not a forced-choice assignment. A single document can provide evidence for multiple hypotheses simultaneously. This preserves the ambiguity that expert Elaborating embraces rather than prematurely resolving.

### 2. Questioning: testing the current frame against evidence

Klein's Questioning is the deliberate search for disconfirming evidence, the check that the current model is not just comforting but supported.

**In the pipeline:** Two methods directly implement Questioning.

**Contradicting evidence detection** (`eval.py::compute_contradicting_evidence_lag`) is the most literal instantiation. For each narrative, the pipeline identifies documents that reference the narrative (keyword match) but do not support its underlying hypothesis (low hypothesis score). These are documents that discuss the claim without providing evidence for it. The metric measures how quickly the pipeline surfaces such contradicting documents after a narrative emerges. The Iranian Mothership result (0-hour lag) demonstrates the system performing Questioning against the dominant narrative on the day it appeared.

**Narrative Velocity Divergence** (`nvd.py::compute_nvd`) is structural Questioning. When NVD exceeds 1.0, the pipeline is flagging that a narrative's spread has outpaced the evidence for it. The implicit question NVD poses is: "Is there enough evidence to justify how fast this narrative is spreading?" On December 11, 2024, NVD answered "no" for the Iranian Mothership narrative (NVD 2.00: narrative spreading at twice the rate of its evidence base).

### 3. Connecting: finding relationships between observations

Klein's Connecting is about discovering that two apparently separate pieces of data are related, that patterns span domains or time periods.

**In the pipeline:** The Source Independence Graph (`independence.py`) instantiates Connecting by tracing the attribution structure across the corpus. It connects documents that share a common origin, revealing whether six different news articles represent six independent observations or one observation repeated six times. The echo-chamber topology it discovered for the Iranian Mothership narrative (6 documents, 6 domains, 0 independent sources) is a Connection finding: all roads lead back to Van Drew.

The composite narrative-capture risk metric (`eval.py::compute_capture_risk`) performs Connecting across methods. It joins IVI (vacuum condition), NVD (narrative-evidence gap), and SIG (independence) to identify when three independent signals converge on the same narrative on the same day. The Dec 11 alert (risk 4.80) is the pipeline Connecting three patterns into a single structural diagnosis.

### 4. Comparing: evaluating competing explanations

Klein's Comparing is the explicit evaluation of alternatives, maintaining multiple hypotheses and checking each against the evidence.

**In the pipeline:** The H1-H5 hypothesis framework is Comparing by construction. Five hypotheses are maintained simultaneously across every document and every time window. The system never collapses to a single explanation. The premature closure resistance metric (`eval.py`, consuming the entropy data from `signals_analyze/storage.py::aggregate_daily_distributions`) measures whether the pipeline maintains its capacity to Compare throughout the event timeline. The empirical result: mean entropy 84.6% of maximum, with the system most uncertain (highest entropy, 96.4%) on the day of maximum narrative chaos (Dec 11). The pipeline Compares most actively when the evidence is most contested.

The evidence-narrative alignment metric is also a Comparing operation: for each time window, it ranks narratives by both volume and evidence support, then correlates the rankings. When the most-amplified narrative is not the most-supported, the system has identified a Comparing failure in the broader information environment.

### 5. Framing: constructing a narrative to organize evidence

Klein's Framing is the act of selecting and committing to a particular way of organizing evidence into a coherent story.

**In the pipeline:** The narrative definitions in `data/nj-drones/narratives.yaml` and their implementation in `nvd.py::NARRATIVE_DEFS` are explicit Frames. Eight narratives, each with a slug, a set of keywords, and a mapping to one of the H1-H5 hypotheses. The pipeline does not generate narratives from data (that would be Framing by algorithm). It applies expert-curated Frames to the corpus and measures their dynamics.

This is a deliberate design choice. At 38 documents, algorithmic narrative generation (HDBSCAN, BERTopic) would overfit. Expert-curated Frames are more defensible and more interpretable. The pipeline measures how Frames interact with evidence, not whether it can produce Frames autonomously.

### 6. Re-Framing: revising the organizing narrative when evidence demands it

Klein's Re-Framing is the most cognitively costly activity: recognizing that the current Frame is inadequate and constructing a new one.

**In the pipeline:** The IVI time series is a Re-Framing signal. When IVI drops (from 15.00 on Dec 21-22 to near zero by Jan 28), the information environment is shifting from a vacuum (no institutional Frame) to a resolution (the Trump White House provides an authoritative Frame). The pipeline does not perform Re-Framing itself, but it detects the structural conditions that should trigger Re-Framing in a human analyst: a closing vacuum, converging evidence, and declining narrative velocity for previously dominant Frames.

The premature closure resistance metric is also a Re-Framing safeguard. By tracking entropy, it ensures that the pipeline's own Frames (the H1-H5 hypothesis distributions) are not locked in prematurely. Even at the resolution event (Jan 28, entropy 1.591 bits), three hypotheses maintain meaningful probability. The pipeline preserves the capacity for Re-Framing even when the institutional Frame has been provided.

## Leveson's STAMP in the pipeline architecture

Leveson's Systems-Theoretic Accident Model and Processes (STAMP, 2012) reframes accidents as control failures rather than component failures. STAMP models systems as control structures where controllers issue commands, receive feedback, and maintain a process model. Accidents occur when the controller's model of the process diverges from the process's actual state.

The pipeline treats the information environment around an ambiguous event as a control system and applies STAMP's diagnostic framework to it.

### The information environment as a control system

| STAMP concept | Information environment analog | Pipeline implementation |
|---|---|---|
| **Controller** | Institutions (FAA, DoD, DHS, elected officials) | Authoritative sources in IVI's denominator |
| **Controlled process** | Public discourse and belief formation | Discourse sources in IVI's numerator |
| **Actuators** | Official statements, press releases, press conferences | Government publications, aviation safety reports |
| **Sensors** | Media monitoring, public comment periods, FOIA | The pipeline itself; also social media as a sensor for public belief state |
| **Process model** | The controller's understanding of public discourse | Not directly observable; inferred from the gap between institutional response and discourse state |
| **Feedback loop** | Information flow from public to institution | Low feedback is visible as sustained high IVI (institutions not responding to discourse excursion) |

### IVI as control loop adequacy

IVI measures the ratio of discourse volume to institutional response. In STAMP terms, this is the adequacy of the feedback loop between the controlled process (public discourse) and the controller (institutions). High IVI means the controller is not issuing corrective commands in proportion to the process excursion. The NJ drones case demonstrated this precisely: from December 11-25, 2024, public discourse expanded rapidly while institutional response remained minimal. IVI peaked at 17.00 (204-doc corpus, 7-day window ending Dec 24). The control loop was inadequate.

When the Trump White House issued its January 28 statement (the actuator firing), IVI dropped. The control loop closed. This is exactly the STAMP pattern: an inadequate control action creates the conditions for process excursion, which creates the conditions for accidents (in this case, narrative capture, citizens firing weapons at the sky, laser strikes on commercial aircraft).

### NVD as process model divergence

In STAMP, the most dangerous failure mode is when the controller's process model diverges from reality without the controller knowing. NVD detects the information-environment analog: when a narrative (the controller's implicit model of what is happening) diverges from the evidence base.

NVD > 1.0 means the narrative is spreading faster than evidence can support it. In STAMP terms, the process model (the narrative) is drifting from the process (the evidence). On December 11, the Iranian Mothership narrative (process model) was spreading at 2x the rate of its evidence (process state). The controller (Van Drew, in this case a political rather than institutional controller) was issuing commands (public statements) based on a process model that was not grounded in available evidence.

### SIG as sensor independence verification

STAMP's control structure assumes that sensors provide independent feedback. If all sensors are reading the same single source, the controller has the illusion of corroboration without its substance. The Source Independence Graph directly tests this STAMP assumption.

For the Iranian Mothership narrative: 6 documents from 6 domains looked like 6 independent sensor readings. SIG revealed they were all amplifying one signal (Van Drew's statement). Independence score 1, amplification 6x. In STAMP terms, the feedback channel had zero independent sensors. The apparent redundancy was illusory. This is exactly the STAMP failure pattern that Leveson describes in aviation safety: multiple instruments wired to the same pitot tube.

### Composite capture risk as unsafe control action detection

STAMP identifies four types of unsafe control actions. The composite narrative-capture risk metric (`eval.py::compute_capture_risk`) detects the information-environment analog: conditions where the controller is likely to issue an unsafe control action (an authoritative statement based on an unsupported narrative).

The convergence condition (high IVI AND high NVD AND low independence) maps to STAMP's hazard analysis:
- High IVI = control loop not providing adequate feedback (constraint violation)
- High NVD = process model diverging from process (model inadequacy)
- Low independence = sensors providing illusory corroboration (feedback degradation)

All three converging on the same narrative on the same day is the structural precondition for an unsafe control action. The December 11 alert (risk 4.80) is the pipeline performing STAMP-style hazard analysis on an information environment in real time.

## What this mapping demonstrates

The Klein and Leveson citations in the abstract are not appeals to authority. They are design constraints that shaped specific engineering decisions:

1. **Hypothesis scores are independent probabilities, not forced-choice classification** (Klein: Elaborating preserves ambiguity)
2. **NVD measures narrative-evidence divergence, not narrative volume** (Klein: Questioning tests the frame; Leveson: process model divergence)
3. **SIG traces attribution, not just citation count** (Klein: Connecting finds hidden structure; Leveson: sensor independence)
4. **Entropy is tracked as a first-class metric** (Klein: Comparing requires maintaining alternatives; Leveson: unsafe control actions arise from premature model commitment)
5. **IVI partitions sources into discourse vs. authoritative** (Leveson: controller vs. controlled process)
6. **Composite capture risk requires three-signal convergence** (Leveson: STAMP hazard analysis requires multiple constraint violations)

The pipeline is not a generic OSINT tool that happens to cite Klein and Leveson. It is a sensemaking system whose architecture was derived from their frameworks. The empirical results validate the architecture, not just the methods built on it.

## Klein-Woods-Bradshaw "Ten Challenges" and the prescriptive advisory layer

Klein, Woods, Bradshaw, Hoffman, and Feltovich (2004) articulate ten challenges that joint human-machine activity must address for the machine to function as a team player rather than as a prosthetic tool. The praxis's prescriptive advisory layer addresses several of these challenges through specific design choices the broader pipeline already commits to:

- **Predictable behavior.** The advisory templates produce deterministic output: the same signal state always yields the same recommendation, traceable to the specific threshold that triggered it. LLM-generated advisories were considered and rejected on this basis; the team-player rubric requires that downstream controllers be able to predict what the system will say next, which an open-ended LLM does not deliver.
- **Observable state.** Each advisory carries the underlying signal values and the STAMP failure-mode classification that produced it. A controller reading the advisory can audit the constraint reasoning, not just the recommendation. This is what makes the advisory layer different from a recommendation engine that says "trust me."
- **Role-appropriate signaling.** Different controllers receive different advisories. STAMP controllers (institutional actors with authority to act) get "act" recommendations; STAMP sensors (media, analysts, researchers) get "monitor" recommendations. Prescribing the same action to all actors ignores the control structure that makes the team work and treats every reader as if they were the primary decision-maker.
- **Bounded autonomy.** The advisory layer proposes; it does not act. Human controllers retain authority over actuation. This is the Horvitz (1999) mixed-initiative pattern, which is the practical instantiation of the team-player rubric for systems where the human must remain accountable for the action taken.

The team-player framing is also why the praxis chose template-based generation over LLM-generation for advisories: predictable, auditable, role-appropriate output is a precondition for joint activity, and the LLM-as-judge failure modes documented in the rapidly accumulating 2024-2025 literature show that LLMs systematically misjudge engineering correctness when not augmented with executable verification. The prescriptive layer's correctness check is the threshold-bound signal state, not the LLM's sense of whether the advisory "looks right."

## References

- Horvitz, E. (1999). Principles of Mixed-Initiative User Interfaces. *Proceedings of the SIGCHI Conference on Human Factors in Computing Systems (CHI 1999)*. [CITE-NEEDED: pagination]
- Klein, G. (2007). Flexecution as a paradigm for replanning, part 2. *IEEE Intelligent Systems*, 22(6), 108-112.
- Klein, G., Moon, B., & Hoffman, R. R. (2006). Making sense of sensemaking 1: Alternative perspectives. *IEEE Intelligent Systems*, 21(4), 70-73.
- Klein, G., Woods, D. D., Bradshaw, J. M., Hoffman, R. R., & Feltovich, P. J. (2004). Ten Challenges for Making Automation a "Team Player" in Joint Human-Agent Activity. *IEEE Intelligent Systems*. [CITE-NEEDED: verify volume, issue, page numbers]
- Klein, G., Phillips, J. K., Rall, E. L., & Peluso, D. A. (2007). A data-frame theory of sensemaking. In R. R. Hoffman (Ed.), *Expertise out of context* (pp. 113-155). Erlbaum. [CITE-NEEDED: verify exact page numbers]
- Leveson, N. G. (2012). *Engineering a Safer World: Systems Thinking Applied to Safety*. MIT Press.
- Leveson, N. G. (2011). Applying systems thinking to analyze and learn from events. *Safety Science*, 49(1), 55-64.
