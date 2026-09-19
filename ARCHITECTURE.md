# Architecture and implementation contract

This is the main-study design. A smaller executable pilot now exists; see IMPLEMENTATION_STATUS.md for the exact boundaries and omissions.

```text
OPTIMIZER PROCESS                         TRUSTED CONTROLLER
train traces → diagnosis → JSON patch ──→ validate scope / budgets
       ↑                                      ↓
       │                                isolated candidate runner
       │                                 train + dev execution
       │                                      ↓
       └── train feedback + decision ←─ immutable evaluator + gate
                                              ↓
                                        versioned incumbent

FINAL TEST: separate evaluator-owned fixtures; accessible only after freeze
```

Use process/storage boundaries, not prompt instructions, to enforce data separation. The task agent receives its task's public inputs and tools, but never evaluator source, expected outputs or other tasks' data. Candidate proposals are data, not executable code. If arbitrary Python mutations become necessary, the project needs a genuinely isolated runner and a revised threat model first.

## Planned project layout

```text
src/roho/
  kernel/          # immutable runner, tool implementation, resource enforcement
  evaluation/      # immutable grader, splits, gates, metrics
  optimization/    # immutable experiment driver, classifier/proposer prompts
  schemas/         # immutable candidate, harness and trace definitions
harnesses/H0.json   # frozen starting values for six mutable components
benchmark/         # generators; public train fixtures only in optimizer mount
private_eval/      # development/test fixtures; evaluator-only mount
experiments/       # frozen manifests and seeds
results/           # append-only trace exports, decisions, summaries
paper/             # LaTeX written after main analysis
```

The directory names above are proposed. An ordinary same-user directory is not a security boundary. For the first version, an immutable controller owns private data and exposes only in-memory virtual tool operations; no candidate may list host files. A later containerized implementation can use read-only fixture mounts and network isolation. Neither replaces auditing the grader.

## Six editable components

| Component | Permitted change | Immutable enforcement |
|---|---|---|
| System prompt | Bounded instruction text | Overall size and output schema |
| Tool policy | Ordering, descriptions, ranking among available tools | Tool names, capability set, argument schema, permissions |
| Context policy | Retrieval count, truncation/selection strategy | No private fixture access; global context ceiling |
| Verification policy | Which public checks to request before completion | Final evaluator and mandatory security checks |
| Recovery policy | Bounded retries, duplicate-action handling | Hard turn/time/token ceilings |
| Task-local memory | What public state to retain within an episode | Reset between tasks; no hidden answer store |

Memory does not persist test task answers into subsequent episodes. Harness evolution is the across-task learning channel; arbitrary answer memorization is not.

## Failure-directed edit masks

| Observed symptom | Permitted component candidates |
|---|---|
| Wrong tool despite available information | Tool policy, prompt |
| Invalid arguments | Tool policy, recovery |
| Missing/repeatedly discarded evidence | Context, memory |
| Weak decomposition / wrong order | Prompt, memory, tool policy |
| Premature or unsupported completion | Verification, prompt |
| Repeated failed actions / exhausted budget | Recovery, context |
| Uncertain attribution or likely capability limit | Abstain; no forced patch |

The classifier returns hypotheses, confidence and trace evidence IDs, not ground-truth causes. Direction masks select which policies may change; immutable tool validation is never weakened. Every learned arm sees the same capped failure-trace sample. B receives raw evidence without the classifier labels or masks. The classification/masking combination is the treatment in C−B.

Use one dominant failure cluster per proposal. If the classifier selects an unsupported class, reject that proposal slot and log why. Avoid expanding the mask silently after a candidate fails validation. Audit a fixed training-only sample of diagnoses manually after the pilot; do not hand-correct main-run diagnoses selectively.

## Candidate contract

Required fields: experiment_id, seed, iteration, candidate_id, parent_sha256, failure_class, evidence_ids, changed_component_values, predicted_effect, predicted_risks, expected_activation.

The controller derives changed_components and diff size; never trusts the model's counts. Only known keys and enumerated safe policies are accepted. Unknown keys, out-of-range values, executable content in config fields, parent mismatch, duplicates and mask violations are rejected. A text prompt can contain hostile instructions, but it cannot alter the controller's permission boundary.

## Trace and ledger contract

For every task attempt, record:

```json
{
  "experiment_id": "required",
  "arm": "required",
  "optimization_seed": "required",
  "attempt_seed": "required",
  "task_id": "required",
  "template_group": "required",
  "split": "required",
  "harness_sha256": "required",
  "model_revision": "required",
  "success": "boolean from external evaluator",
  "termination_reason": "enum",
  "input_tokens": "integer from runtime",
  "output_tokens": "integer from runtime",
  "steps": "integer",
  "wall_seconds": "monotonic measurement",
  "tool_events": "structured records",
  "activation_events": "emitted by trusted runtime",
  "failure_hypothesis": "nullable classifier record",
  "infrastructure_status": "enum"
}
```

This is a field specification, not an example measured run. Numeric fields must become actual typed numbers in the executable schema.

A separate optimizer ledger records classifier/proposer tokens, rejected proposals, evaluation resources, gate comparisons, prior and next hashes, selection rank and promotion reason. Never allow a candidate to report its own success or write its evaluator ledger.

## Algorithm contract

```text
Freeze H0, trusted kernel, data splits, resource ceilings and analysis.
Evaluate H0 on train and development with the fixed attempt seeds.
For each of five iterations:
    Build bounded evidence from training failures only.
    Generate three candidates (diagnosis/masks depend on arm).
    Validate each candidate; rejected proposals still consume slots.
    Evaluate valid candidates under identical protocol and ceilings.
    Apply the common eligibility rules and arm-specific gate.
    Select one eligible winner using the fixed ordering, or keep H.
    Record the complete transition and resource usage.
Freeze the final incumbent for every arm and optimization seed.
Run the single prespecified final-test batch and analyze without tuning.
```

## Implementation sequence and acceptance tests

1. Benchmark plus immutable grader. Test reference answers and wrong artifacts, path isolation, state reset, deterministic normalization and resource failures.
2. H0 and model adapter. Confirm actual token counts, structured calls, reproducible configuration and complete trace capture. No optimizer yet.
3. Gate logic tests. Include aggregate improvement with individual loss; no prior successes; unchanged candidate; lower tokens with unchanged success; cap violations; mismatched task IDs; and repeated-attempt pairing.
4. Candidate schema, diff counter and allowlist. Test whitespace-only changes, hidden extra keys, component-count violations, per-component token limits and evaluator-edit attempts.
5. Classifier and proposer. Test abstention, diagnosis failures, duplicates and failed proposals; no hidden free retry loops.
6. Disjoint feasibility pilot and resource projection. Freeze main configuration only after this passes.
7. Main runs; sealed final batch; analysis; then LaTeX manuscript and source package.

Do not build a UI, distributed scheduler, general shell agent, or more model families before this sequence works.
