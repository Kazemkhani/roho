# ROHO Kaggle smoke result — 20 September 2026

This directory contains the first corrected real-model ROHO smoke artifact. It is exploratory feasibility evidence, not a paper result.

## Integrity and environment

- Artifact: `roho-smoke-results.zip`
- Size: 34,514 bytes
- SHA-256: `4d0eafcb592394c8e61868537de1eb7b13de0ffb311f6e2582757e9b1f81efbd`
- Backend: local Hugging Face inference
- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Resolved revision: `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- Runtime: free Kaggle Tesla T4, Torch 2.10.0+cu128, Transformers 4.57.6
- Precision: float32 on `cuda:0`
- Frozen-run hash: `e7f82d744dbf75802ddd34ea9bf3bd513337529af27b712f2cf48e67d4abd228`

`unzip -t results/roho-smoke-results.zip` validates every member. The ZIP contains the report, state/freeze manifest, environment and model records, model-call ledger, test summary/outcomes and 30 episode traces.

## Corrected result

| Arm | Test success | Lost / baseline solved | Mean tokens | Search tokens |
|---|---:|---:|---:|---:|
| A — fixed | 3/5 (60%) | 0 / 3 | 602.6 | 0 |
| C — failure-directed, aggregate gate | 3/5 (60%) | 0 / 3 | 602.6 | 918 |
| D — failure-directed, task gate | 3/5 (60%) | 0 / 3 | 602.6 | 918 |
| E — task gate + one-component budget | 3/5 (60%) | 0 / 3 | 602.6 | 918 |

The learned arms are identical to A because every generated proposal was rejected. Qwen returned valid JSON but used a forbidden nested `agent_harness/new_value` schema instead of direct component-to-value edits. ROHO therefore made no change, which is the correct fail-closed behavior.

## Excluded diagnostic attempt

The first T4 attempt used float16. Its sampling path produced non-finite probabilities; a temporary sanitizer prevented the CUDA exception but revealed uniformly corrupted `!`-only generations. That output was not interpreted as model capability and was replaced. The committed adapter uses float32, and the notebook now requires a sane generation preflight before opening a run.

## Interpretation and next decision

The corrected run establishes that the private Kaggle path, model download, GPU inference, checkpoints, freeze gate, held-back test opening, reporting and artifact export work end to end. It does **not** show self-improvement, regression reduction or superiority of any arm. Five test tasks and one seed are descriptive only.

Before another run, freeze a stricter schema-constrained classifier/proposer prompt and use a fresh dataset seed/test batch. Do not tune against the already opened cases in this artifact. The larger pilot should wait until a new smoke run demonstrates a non-trivial admissible-proposal rate.
