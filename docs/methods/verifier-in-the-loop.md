# Verifier-in-the-loop architecture: AI-assisted-math patterns for TELL

*Reference material. Documents architectural patterns from formal-math systems that map onto TELL's signal-and-advisory pipeline. Future-work guidance, not implementation specification.*

**Status:** [REVIEW] Working reference document, 2026-05-05. Companion to `research/synthesis/2026-04-27-endless-forge-delta-library.md` Section A and to the integration plan at `research/synthesis/2026-05-05-compendium-integration-plan.md`.

## Purpose

Catherine Havasi's Endless Forge framing positions AI-assisted formal mathematics as the architectural reference for typed composition with verifier-in-the-loop synthesis. The praxis already implements this pattern at coarse grain: LLMs propose narrative classifications, hypothesis scores, and contextual interpretations; threshold-bound checkers verify the output; humans retain authority to act. This document records the specific architectural patterns from formal-math systems (Lean, Mathlib, LeanDojo, Sledgehammer, AlphaProof, Goedel-Prover-V2) that map onto TELL's pipeline, so any future HITL evaluation surface (the Uncertainty Game scenario engine, an advisory editor, an evaluation dashboard) can start from a coherent template rather than rediscover the architecture.

This is reference material, not implementation specification. The praxis does not need any of these patterns to deliver TMP 2026, and the substrate-vs-specialization framework merged in PR #55 explicitly bounds what the open praxis can claim about commercial implementations. Treat this catalog as the bibliography of architectural moves available to future development sessions.

## The core pattern

Across the formal-math systems surveyed in DELTA Section A, a common architectural pattern recurs:

1. **Typed library.** A curated, machine-readable corpus of components with explicit interface contracts. In Lean, this is Mathlib (over 12,000 typeclass instances as of 2022). In TELL, this is the narrative library (`data/nj-drones/narratives.yaml`), the controller library (`controllers.yaml`), and the H1-H5 hypothesis space.

2. **LLM proposes.** A language model proposes candidate compositions: tactics, proof sketches, or completions. In LeanDojo's ReProver, this is retrieval-augmented tactic generation. In TELL, this is the LLM that proposes per-document hypothesis scores via `signals_analyze/hypothesis_scoring.py`.

3. **Verifier checks.** An automated verifier rejects compositions that do not satisfy the interface contracts. In Lean, this is the kernel typechecker. In TELL, this is the threshold-bound signal-state checker that decides whether to fire the composite capture-risk alert.

4. **Human accepts or repairs.** When the verifier rejects, the human (or a higher-level automated process) repairs the proposal. In Lean Copilot, the user accepts or rejects suggested tactics. In TELL, the prescriptive advisory layer's role-differentiated output gives the controller the information needed to repair the institutional response (issue a statement, cross-check sources, verify independence).

The pattern is not LLM-as-judge. It is verifier-as-judge with LLM-as-proposer and human-as-decider.

## Specific patterns mapped to TELL

### Premise selection (LeanDojo / ReProver, Magnushammer)

Premise selection in formal math is the problem of, given an open goal, retrieving from a library of thousands of lemmas the small subset most likely to close it. ReProver (Yang et al., NeurIPS 2023) trains a retrieval-augmented LLM that combines semantic embedding with proof-state context. Magnushammer (Mikuła et al., 2023) shows that contrastive-learned embeddings outperform traditional k-NN retrieval.

The TELL analog: given a signal state (high IVI, NVD divergence on narrative X, low SIG independence), retrieve from the narrative library the narratives most likely to be at risk of capture, and from the controller library the controllers most likely to need to act. The praxis currently does this by exhaustive scoring across the full narrative set. A premise-selection model would scale this to corpora with hundreds of narratives and thousands of controllers without compromising recall on the small set that matter.

Implementation hook (future): a contrastive embedding over (narrative, signal-state, controller-jurisdiction) tuples, trained on validation case ground truth.

### Hammers (Sledgehammer, CoqHammer, Lean's `aesop`)

A hammer in formal math is a one-click tool that selects a small subset of relevant lemmas, runs an external automated theorem prover (Vampire, E, Z3) against the goal, and reconstructs the proof in the proof assistant when the prover succeeds. Sledgehammer for Isabelle/HOL is the canonical implementation.

The TELL analog: given a partial advisory (signal state plus controller jurisdiction), automatically synthesize the full role-differentiated recommendation by composing relevant components from the narrative library and the available-actions list. The current prescriptive layer is template-based; a hammer-style synthesizer would generalize beyond the templates by composing primitive advisories under explicit rules.

Implementation hook (future): out of scope for TMP 2026. The template-based approach is sufficient for the demo and is more auditable than a synthesis approach. Worth revisiting if a manufacturing-composition or self-driving-labs instantiation surfaces a richer action space than the templates can express.

### Subgoal decomposition (DeepSeek-Prover-V2)

DeepSeek-Prover-V2 (arXiv:2504.21801, May 2025) decomposes a theorem into a sequence of subgoals via a frontier LLM, then discharges each subgoal with a smaller specialist prover, then reassembles the proofs. The smaller prover sees only one subgoal at a time and runs much faster than the frontier model would.

The TELL analog: decompose an adversary-capability claim into specialized sub-checks. For an OSINT case, this is (a) source-attribution check via SIG, (b) narrative-evidence-divergence check via NVD, (c) institutional-response-gap check via IVI, and (d) hypothesis-distribution check via SQM. Each check runs independently. The composite is reassembled at the prescriptive layer.

This is what TELL already does, structurally. The DeepSeek-Prover-V2 architecture surfaces the pattern explicitly and gives it a name: subgoal decomposition with specialist discharge.

### Lean Copilot (Song, Yang, Anandkumar et al., 2025)

Lean Copilot embeds an LLM inside Lean via FFI, providing `suggest_tactics`, `search_proof`, and `select_premises` as in-editor commands. The user chooses when to invoke the LLM, the LLM proposes, Lean checks, the user accepts or refines.

The TELL analog: a HITL evaluation surface where an analyst reviews a draft advisory, requests an LLM-suggested refinement, sees the threshold-bound signal state that justifies the refinement, and accepts or refines further. The Uncertainty Game scenario engine is the natural home for this pattern: the human player makes sensemaking decisions; the AI proposes alternative interpretations the player may or may not accept; the underlying STAMP control structure verifies that any accepted interpretation respects the constraints of the role.

This is the most directly transferable pattern in the catalog and the one the integration plan flags for the artifact-design bibliography PR (deferred per JMill's 2026-05-05 review).

### Verifier-guided self-correction (Goedel-Prover-V2)

Goedel-Prover-V2 (arXiv:2508.03613, 2025) uses verifier rejection as a training signal: when the formal verifier rejects a proof, the rejection diagnostic is fed back as cold-start RL data to teach the model to repair the rejected step. The 32B model reaches 88.1 to 90.4 percent on MiniF2F at much smaller compute than the frontier provers.

The TELL analog: when the threshold-bound checker rejects a proposed advisory (because the signal state does not actually warrant the recommendation), the rejection becomes training data for refining the LLM that proposes advisories. The praxis does not currently train a model from rejection signals; the prescriptive layer is template-based by design. But for any future advisory that uses LLM-generation under a verifier check, this is the canonical training pattern.

### Test-time RL on problem variants (AlphaProof)

AlphaProof at IMO 2024 generated millions of related problem variants at inference time and learned from them, producing a "characterized envelope" of buildable proofs for each problem. The compendiums frame this as the closest formal analog of the praxis's "characterized envelope of buildable designs" claim.

The TELL analog: at evaluation time, sample adversarial perturbations of the warfighter signal (the signal state plus the case context) and characterize the envelope of advisories the system would produce. This is a robustness check beyond the current threshold-bound check: not "does the advisory fire on this signal state," but "does the advisory remain stable under small perturbations of the signal state." This connects directly to the Wasserstein DRO substrate documented in `dev/tell/docs/methods/uncertainty-formalisms.md`.

## Constraints: what NOT to use this for

The verifier-in-the-loop pattern is powerful but easily abused. Three constraints apply:

1. **The verifier is the threshold-bound checker, not another LLM.** The LLM-as-judge failure modes documented in Zheng et al. 2023 and the position-bias literature show that LLMs systematically misjudge engineering correctness when asked to evaluate other LLMs' output. The praxis's threshold-bound signal-state check is the verifier; an LLM-evaluating-LLM loop is not.

2. **Templates beat synthesis when auditability matters.** The current prescriptive layer is template-based. Hammer-style synthesis is more flexible but harder to audit. For high-stakes advisories (institutional response to capture-risk conditions), auditability wins.

3. **Bounded autonomy.** The verifier-in-the-loop pattern proposes; the human accepts or refines. The praxis maintains this bound rigorously. Any future evaluation surface (the Uncertainty Game, an advisory editor) must preserve it.

## Future-work hooks

Three potential development tracks emerge from this catalog:

- **Premise selection over the narrative-and-controller library.** Train a contrastive embedding for retrieval over the typed library at signal-evaluation time.
- **HITL evaluation surface for the Uncertainty Game.** Lean-Copilot-style in-game interaction where the player composes interpretations and the underlying STAMP structure verifies them.
- **Test-time robustness check on advisories.** Sample Wasserstein-bounded perturbations of the signal state and characterize the envelope of advisories. Connects to `dev/tell/docs/methods/uncertainty-formalisms.md`.

None of these are committed work. They are reference architecture for future sessions.

## References

- Mikuła, P., Tworkowski, S., Antoniak, S., et al. (2023). Magnushammer: A Transformer-Based Approach to Premise Selection. arXiv preprint. [CITE-NEEDED: verify exact authors, venue, arXiv ID]
- Song, P., Yang, K., Anandkumar, A., et al. (2025). Lean Copilot: LLMs as Copilots for Theorem Proving in Lean. arXiv:2404.12534. [CITE-NEEDED: verify full author list]
- Yang, K., Swope, A., Gu, A., Chalamala, R., Song, P., Yu, S., Godil, S., Prenger, R., & Anandkumar, A. (2023). LeanDojo: Theorem Proving with Retrieval-Augmented Language Models. *NeurIPS 2023*. arXiv:2306.15626.
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench. *NeurIPS 2023*. [CITE-NEEDED: verify full author list, exact title, pagination]

The AlphaProof, Goedel-Prover-V2, DeepSeek-Prover-V2, and Sledgehammer references are catalogued in `research/synthesis/2026-04-27-endless-forge-delta-library.md` Section A.
