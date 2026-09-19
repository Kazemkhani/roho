# ROHO experimental protocol v0.1

Status: prospective draft, 19 September 2026. No ROHO experiments have run. Numerical settings below are proposed design choices, not measured results. Freeze v1 after a disjoint feasibility pilot and before accessing main-test outcomes.

Implementation update: the user selected free Kaggle compute. The repository now includes an exploratory pilot; consult IMPLEMENTATION_STATUS.md for differences from this prospective main protocol. Mock unit tests are software validation, not ROHO LLM results.

## 1. Scope and hypothesis

Working title: **ROHO: Task-Level Regression Constraints for Budgeted Agent-Harness Optimization**.

Primary RQ: At the same search-resource ceilings, does a task-level retention gate reduce final unseen-task regression compared with aggregate non-decrease, without materially sacrificing task success or increasing task-time token use?

Primary hypothesis H1: Arm D has lower final anchor regression than C, with test success no more than 5 percentage points lower and mean task-time tokens no more than 10% higher. These are proposed practical margins, not established clinical or industry thresholds. A small study may be unable to demonstrate this joint hypothesis precisely.

Secondary questions:

- H2: How do one-, three- and all-component edits change acceptance, regression, success and optimization cost? No prespecified claim that smaller is always better.
- H3: Does the combination of failure classification and an enforced edit mask outperform unguided proposals? This contrast tests that combination, not classification independently.
- Exploratory: Which components change, actually activate, and coincide with improved outcomes? Observational counts are not causal attribution.

No foundation-model training, recursive meta-evolution, arbitrary host execution, patient data, clinical deployment, or primary cross-model-transfer claim. One frozen local task model and the same frozen model in the proposer role suffice for the first experiment. A stronger proposer is a separately labeled extension, held fixed across arms.

## 2. Why aggregate improvement is insufficient

Let y_i(H) be the immutable evaluator's binary result for task i. On n tasks:

S(H) = (1/n) sum_i y_i(H).

For parent H and candidate H', let G count 0→1 changes and F count 1→0 changes. Then:

S(H') − S(H) = (G − F)/n.

Consequently, positive net success permits F > 0. Example, **illustrative, not empirical**: a parent solves 60/100 cases; a candidate gains 10 previously failed cases and loses 5 old successes. It reaches 65%, but regresses on 5/60 = 8.33% of the parent's successes.

This elementary identity motivates the measurement; it is not claimed as a novel theorem.

## 3. Benchmark and isolation

Main benchmark: 300 procedurally instantiated deterministic tool tasks, split into 120 optimization, 60 development/gate, and 120 untouched final-test tasks. Five families contribute 60 tasks each, allocated 24/12/24 per family.

| Family | Example task contract | Deterministic check |
|---|---|---|
| Filesystem artifacts | Transform a fixture into a specified output file | Normalized content plus final path/state |
| Structured retrieval | Join facts across small JSON documents | Exact answer and required source identifiers |
| Calculation | Compute a specified rational or decimal quantity | Exact rational or declared tolerance |
| Table queries | Filter, aggregate or join a small fixture | Canonicalized row set and schema |
| Multi-tool workflows | Retrieve → compute → write → verify | Final artifact plus required state invariants |

Use virtual filesystem and constrained operations initially; do not expose the user's shell. This intentionally replaces the proposed unrestricted shell category. The scope is tool-agent reliability, not general terminal proficiency.

Split by **template groups / solution structure**, not only numeric seeds or filenames. Aim for at least 12 independently authored template groups per family: four optimization groups with six instances each, two development groups with six instances each, and six test groups with four instances each. Pilot templates are separate. These 60 groups are a design target requiring audit, not currently existing data. Report both task and group counts; templated instances are not independent research problems.

The proposer sees optimization prompts, tool traces, public error codes and final training grades, but not hidden expected answers. Gate cases and traces stay in an evaluator-owned process. Proposer receives promotion decisions, not task-specific gate errors. The final test is inaccessible to the proposer, candidate runtime, analyst dashboards and tuning scripts until all final candidates and analysis code are frozen. A filename such as `hidden_test.json` does not itself enforce isolation.

Development decisions inevitably reveal information; call this set **development**, never unbiased held-out evidence. A separate test is necessary because adaptive reuse can overfit validation. [Dwork et al.](https://arxiv.org/abs/1506.02629v2)

Benchmark checks before optimization: reference solver passes every task; malformed outputs fail; irrelevant extra artifacts cannot satisfy the contract; no answer leakage through tools; traversal/symlink escapes rejected; fresh state per task; equivalent parameterizations have consistent grading. Do not plant only flaws that the proposed ROHO operators are designed to repair.

## 4. Six primary arms

All learned arms share model, starting harness, candidate count, decoding settings, data, cost ceilings, trace format and promotion objective. Component definitions are fixed before search.

| Arm | Proposal guidance | Development gate | Max changed components |
|---|---|---|---:|
| A | None; fixed H0 | None | 0 |
| B | Raw failure traces; no classification or edit mask | Aggregate non-decrease | 3 |
| C | Failure-directed, enforced component mask | Aggregate non-decrease | 3 |
| D | Same as C | Task-level zero observed loss | 3 |
| E | Same as C | Task-level zero observed loss | 1 |
| F | Same as C | Task-level zero observed loss | All 6 |

Primary contrast D−C isolates gate type. E−D and F−D address edit budget within directed, task-gated search. C−B addresses guided proposal generation at the same component ceiling. A measures net improvement against no optimization.

This is not a full factorial design; it cannot identify all gate-by-budget interactions. “All” means no additional component-count restriction inside the same six-component language; it does not mean permission to rewrite arbitrary Python or the evaluator.

Prompt-only optimization is a useful optional seventh arm, but not a substitute for the gate-matched baseline. A pinned GEPA adapter is the preferable external extension when resources allow. Do not name B “GEPA” or C “Self-Harness”: they are mechanism baselines, not faithful replications.

## 5. Candidate representation and mutation budget

H has six logical components: prompt, tool policy, context policy, verification policy, recovery policy, and task-local memory policy. They are JSON/text values interpreted by an immutable runtime. The last five choose among documented safe operations and bounded parameters; no candidate-provided Python, `eval`, imports, network destinations, or executable strings.

D(H,H') = number of logical components whose canonicalized values differ.

Require D ≤ B, with B = 1, 3 or 6. Canonicalization ignores whitespace and key ordering, but not text content. Hold a common maximum of 256 changed tokenizer tokens per component and 1,536 total changed tokens per candidate. Declare the edit-distance implementation and tokenizer at freeze. Also cap total serialized harness size at 4,096 model tokens. Component count is not semantic distance: a small textual change can radically change behavior.

All candidates include a parent hash, patch, target failure hypothesis, predicted improvement, predicted regression risks and expected activation event. The controller computes the actual diff and validates bounds independently. Invalid or duplicate proposals consume their proposal slot; do not let one arm silently resample until it produces useful candidates.

## 6. Common promotion objective and gates

Use constraints and an interpretable ordering, rather than a weighted sum of incompatible raw units. Report a quality–cost frontier; do not introduce weights selected after results.

For candidate H' relative to incumbent H, common eligibility requires:

1. Schema, immutable-boundary, resource and execution-validity checks pass.
2. S_train(H') ≥ S_train(H).
3. Mean task-time tokens across all train+dev attempts are ≤ 1.10 times H0's mean on that same set. Failed attempts count.
4. Either S_train improves strictly, or S_train ties and mean train token use falls by at least 5% relative to H.

Aggregate gate for B/C: S_dev(H') ≥ S_dev(H).

Task gate for D/E/F: no development task-attempt solved by H becomes failed by H'. Equivalently, the lost-success count F_dev must equal zero. Retention is checked on matched task/attempt identifiers, not just a rounded percentage. If the incumbent has zero development successes, retention is uninformative: record “not estimable” and fail the feasibility criterion rather than claiming safety.

Among eligible candidates, order by higher train success, then lower train mean tokens, then lower serialized harness size, then canonical candidate hash. Promote at most one candidate per iteration; do not merge independently accepted patches without evaluating the merged harness. If none qualifies, keep H unchanged. This is a local constrained search, not a global argmax over all possible harnesses.

The 10% cap bounds tolerated overhead; it does not imply cost reduction. A claim of cheaper inference requires measured test cost reduction. Structural size is a complexity proxy, not a proof of maintainability or safety. Latency remains a reported outcome, not another tunable weight.

## 7. Iterations, stochasticity and resource matching

Main proposal: five iterations, three candidate slots per iteration, three optimization seeds. Use the same initial task model, proposer model, quantization, runtime, public tool descriptions, context ceiling and per-task step limit across arms. Proposer seeds control candidate variability. Record all decoding parameters; greedy task decoding does not guarantee bitwise determinism across hardware or backend versions.

Evaluate every valid candidate on the entire train and dev sets; no arm gets favorable early screening. Invalid proposals use their slot but incur no fictitious rollouts. Record actual consumed resources and common ceilings. Pair each arm's run with the same seed identifiers; their adaptive trajectories may nevertheless diverge.

On a disjoint pilot, test repeated H0 executions. If task outcomes are reproducible, cache incumbent outcomes keyed by full harness/model/environment/task hashes. Otherwise freeze at least two matched task-attempt seeds for all gate evaluations and report repeat-level and task-level summaries. Do not turn repetition into best-of-k scoring. Unexplained backend instability blocks caching.

Two matched budget controls are needed: candidate/evaluation ceilings and a common total model-token ceiling including proposer, classifier, target agent, verification and failed candidates. Choose the token ceiling using pilot measurements before main runs. The directed methods pay for their classification calls. Stop before launching work whose worst-case allowance would exceed the remaining ceiling. Unused allowance is reported, not spent on extra candidates. Thus these are **matched ceilings**, not a claim of identical realized computation.

Common provisional task limits: 12 model/tool steps and 512 new tokens per model turn. Choose a feasible input-context ceiling and wall-time timeout in the pilot and freeze them. Log input and output tokens separately: their computational costs differ. API dollars are irrelevant for free offline calls; do not equate token counts with energy or monetary cost. Record wall-time and hardware; energy only if directly measured.

### Compute size, before repeats

With all candidates valid, each learned arm uses 5 × 3 × (120+60) = 2,700 candidate-task episodes. Share a 180-episode H0 baseline within each seed where caching is valid. Five learned arms and six final harnesses give:

3 seeds × [180 + 5×2,700 + 6×120] = **43,200 task episodes**.

At 12 turns per episode this is up to 518,400 target-model turns, excluding proposal and diagnosis calls. Two evaluation attempts double task episodes to 86,400. This is not a “little test.” No wall-time or monetary estimate is credible before throughput measurement.

Smoke pilot: 24 train, 12 dev and 24 separate test tasks; A/C/D/E; two iterations; two candidates; one seed; one attempt. Maximum episode count is 36 + 3×2×2×36 + 4×24 = **564**, plus proposal calls. Pilot-test results are exploratory and cannot become the main test. An even smaller plumbing test may run first.

## 8. Metrics and final analysis

Record task success; task-time input/output tokens and total; steps; tool error count divided by attempted calls; median and p95 end-to-end latency; harness tokens and changed components; proposal validity; acceptance fraction; and total search tokens/time, including all rejected work.

Step regression:

R_step(H,H') = count[y_i(H)=1 and y_i(H')=0] / count[y_i(H)=1].

Final anchor regression replaces H with frozen H0 and H' with the selected final harness. Report counts and denominators. A zero denominator yields NA, not zero. Also report the gained-success count, lost-success count, and their task-family distribution.

The primary final endpoint is the paired difference in anchor regression D−C on the untouched test; success and mean-token contrasts are companion endpoints for H1. Final test execution is one frozen batch across all prespecified arms/seeds/repeats. “Once” means no tuning after observing outcomes, not prohibition of predeclared repetitions. Select each seed's final harness before opening that batch; report all seeds, not the best seed.

Use paired resampling of task-template groups within families for uncertainty conditional on each trained harness; keep all instances of a group together and retain arm pairing. Report seed-specific estimates and between-seed range. With only three search seeds, do not present tight population-level uncertainty over optimizer randomness. A nested seed/group bootstrap can be supplemental with this caveat. Predeclare 10,000 bootstrap replicates and their RNG seed in the frozen analysis script.

H1 is supported only if the upper confidence limit for D−C regression is below zero, the lower success-difference limit is above −0.05, and the upper mean-token-ratio limit is below 1.10. Otherwise report inconclusive or contradicted findings. Handle undefined denominators explicitly. Secondary contrasts are exploratory; any family of secondary significance tests must be multiplicity-adjusted, not cherry-picked. No post-hoc weight selection or winner selection on test.

The 120-task test, drawn from only 30 test template groups, is a small study. A 5-point success change equals six tasks before repeats; power depends strongly on paired discordance and group correlation. Perform prospective precision/power simulations from pilot-only assumptions before freezing the main sample size. If inadequate, enlarge the untouched test before collecting its outcomes or label the study exploratory.

Do not use IE = ΔSuccess/(ΔCost + λRegression): its denominator can be zero or negative. Instead report the vector (success gain, regression, inference tokens, optimization tokens). Optionally report percentage-point gain per million **total positive search tokens** at prespecified checkpoints. For deployment savings, report break-even tasks only when inference savings are positive, and only within comparable models/token accounting; prefer measured compute time when input/output mixes differ.

## 9. Why zero observed regression is not a guarantee

The gate can ensure only that the measured development outcomes satisfy its predicate. It cannot guarantee unseen-task retention, correctness of an incomplete evaluator, immunity to distribution shift, or future sampling stability.

For a fixed, independently assessed candidate and n independent baseline-solved cases with zero losses, a one-sided 95% binomial upper bound is 1 − 0.05^(1/n). With n=60 this is about 4.87%; at least 299 such independent cases are needed to put the bound below 1%. These conditions do **not** hold automatically for templated tasks, repeated attempts, or adaptively reused development gates. Do not attach this guarantee to ROHO's gate. This calculation is a sample-size illustration, not observed evidence.

Per-step zero losses implies preservation on the same fixed deterministic gate cases across accepted updates; it says nothing about a separate task distribution. Track anchor regression on the final test precisely to measure this gap.

## 10. Failure and integrity rules

- Treat agent-induced errors, invalid calls, exhaustion and model timeouts as failures with consumed cost included.
- Classify infrastructure failures using immutable criteria; allow at most one automatic retry, log both attempts and charge their resources. Never relabel an inconvenient agent failure as infrastructure noise.
- If a shared fixture is defective, invalidate the affected paired block across all arms using the same rule. Keep the original record; do not silently drop hard cases.
- The internal completion verifier is a mutable policy, but the final success evaluator and permission checks are immutable and independent. Disabling internal verification cannot make an incorrect artifact pass.
- No per-test-task patching, handcrafted repair added to only the proposed method, or undisclosed human candidate selection.
- Hash datasets, seeds, manifests, evaluators, model weights/revision, runtime configuration and all harness versions. Log accept/reject reasons outside candidate write access.

## 11. Freeze checklist and stopping decisions

Before main runs, record: model/proposer IDs and revisions; license permissions; quantization; runtime version; baseline hash; task-generator and split hashes; six component schemas; tokenizer/edit-distance definition; context, token and time limits; repeat count; common search-token ceiling; analysis hash; and exclusions fixed from the pilot.

Feasibility gates: all reference checks pass; no boundary violation is accepted; model reliably emits the action schema; enough baseline successes exist to estimate retention; failures are not all fundamental model incapacity; and projected runtime fits approved resources. Operational screening targets are 20–80% H0 success on the disjoint pilot and at least ten solved pilot development task-attempts. These targets select a feasible study, not evidence of ROHO effectiveness; log model/task revisions made in response.

If gains vanish, gates block almost all changes, or cost increases, retain and report that result. If the tiny cached model cannot propose valid edits, use it only for software smoke testing and seek a more capable approved local model. Do not substitute scripted oracle “improvement” while claiming LLM self-improvement.
