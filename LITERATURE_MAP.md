# Literature map and novelty audit

Accessed 19 September 2026. This is a targeted screening review, not a systematic review or proof that no overlapping paper exists. Sources are primary papers. “Unverified” means not established in this review, **not absent**. Code availability below refers to what the inspected source reports, not a successful installation or reproduction. Current unversioned links must be pinned to exact versions before the experiment freeze.

## Fifteen-paper map

| Work and inspected source | Optimized object and feedback | Search / selection mechanism | Regression relevance | Code status / inspection depth |
|---|---|---|---|---|
| [Self-Harness, v3](https://arxiv.org/html/2606.09498v3), 2026 | Harness; clustered failed execution traces | Parallel targeted minimal edits; split-wise pass-count acceptance | Explicit regression tests; aggregate non-decrease can still conceal individual lost successes | Code linked from abstract page; methods §§3.2–3.4 inspected |
| [Agentic Harness Engineering, v4](https://arxiv.org/html/2604.25850v4), 2026 | Tools, middleware, memory, prompts; observable trajectories | Edit predictions checked against later outcomes; attribution and rollback | Regression-aware edit attribution, not merely blind success maximization | Repository availability not audited; algorithm and attribution inspected |
| [Code as Agent Harness](https://arxiv.org/html/2605.18747), 2026 | Survey / agenda for executable agent systems | Not one optimization algorithm | §5.2.3 explicitly discusses non-regressing self-evolution, contracts and invariants | Not an implementation baseline; relevant agenda section inspected |
| [AI Harness Engineering](https://arxiv.org/abs/2605.13357), 2026 | Runtime substrate and responsibility taxonomy | Four-level harness ladder; trace-based evaluation | Verification and accountability motivate ROHO's boundaries | Code unverified; abstract and framework overview inspected |
| [Hierarchical Self-Improvement](https://arxiv.org/html/2608.08466), 2026 | Task harness and evolver strategy; environment rewards | Hierarchical evolution, version pool, immutable outer anchor | Scope isolation and held-out evaluation; feedback and backbone limitations | Code linked from abstract; architecture and evaluation passages inspected |
| [Retrospective Harness Optimization, v3](https://arxiv.org/abs/2606.05922v3), 2026 | Harness; retrospective trajectories without ground-truth optimization labels | Coreset, parallel reruns, diagnosis, pairwise self-preference | Different feedback setting; not evidence for deterministic task retention | Code linked; abstract and compute-accounting appendix inspected |
| [HarnessFix, v2](https://arxiv.org/html/2606.06324v2), 2026 | Harness flaws; trace-to-implementation attribution | Scoped repair operators and repair specifications | Validation explicitly considers regressions on previously solved tasks | Paper links HarnessFix/HarnessFix; §§III-C–III-D inspected |
| [HarnessBank, v2](https://arxiv.org/html/2607.13683v2), 2026 | Harness; diagnosis indexed by component and failure pathology | Semantic archive; validity, activation and significance screening | Paired outcome testing and untouched final test; overlaps with trustworthy promotion | Abstract promises code upon acceptance; §§3.1–3.3 inspected |
| [Meta-Harness](https://arxiv.org/abs/2603.28052), 2026 | Harness code; prior source, scores and execution traces | Agentic outer-loop code search | Quality and context-token efficiency already considered | Official project/repository surfaced in search; abstract inspected, regression details unverified |
| [AutoHarness](https://arxiv.org/abs/2603.03329), 2026 | Action-validity harnesses and code policies | Iterative synthesis using game feedback | Enforcing action validity differs from preserving previously solved tasks | Code unverified; abstract inspected |
| [HarnessOpt-Bench](https://arxiv.org/abs/2608.06301), 2026 | Optimizer capability; graded target-agent evaluation | Fixed evaluation budget; nominated final candidate | Trusted evaluation boundary, resource metering and inaccessible test partition | Code unverified; abstract inspected; candidate external evaluation source |
| [GEPA, v2](https://arxiv.org/abs/2507.19457v2), 2025/2026 | Prompt modules; textual trajectory feedback | Reflective mutation and Pareto-based candidate evolution | Preserves diverse task strengths; not equivalent to a zero-loss gate | Code linked; abstract, algorithm description and official API documentation inspected |
| [Automated Design of Agentic Systems, v2](https://arxiv.org/abs/2408.08435v2), 2024/2025 | Agent programs; execution performance and archive | Meta Agent Search | Establishes automated agent design and transfer as prior art; exact retention constraint unverified | Project linked; abstract inspected |
| [AFlow, v4](https://arxiv.org/abs/2410.10762v4), 2024/2025 | Code-represented workflows; execution feedback | Monte Carlo tree search | Cost-effective workflow discovery predates ROHO; exact retention constraint unverified | Code linked; abstract inspected |
| [Generalization in Adaptive Data Analysis and Holdout Reuse, v2](https://arxiv.org/abs/1506.02629v2), 2015 | Validity of adaptively selected analyses | Theory and reusable-holdout mechanisms | Reusing a gate set adaptively does not make it an untouched test set | Theory reference, not a harness implementation; abstract inspected |

## What changes in the original proposal

The six supplied arXiv paper identifiers resolve to the stated works. However, the proposed novelty understates their overlap with ROHO.

Self-Harness §3.4 accepts an edit when neither evaluation split loses aggregate passes and at least one gains. Its minimal, failure-grounded edits are already central to its method. This makes a “first failure-directed regression gate” claim untenable. Its gate split also participates in selection; ROHO must distinguish development gating from a final independent test. [Source](https://arxiv.org/html/2606.09498v3)

HarnessFix is even closer to the proposed failure-to-component mapping: it uses scoped repair operators and validates against losses on previously solved tasks. Therefore, **even task-level regression protection is not a new idea by itself**. [Source, §§III-C–III-D](https://arxiv.org/html/2606.06324v2)

HarnessBank additionally screens for working evaluation infrastructure, actual activation of the change, and paired evidence of benefit. ROHO cannot claim the first statistically informed or evidence-based harness promotion mechanism. [Source, §3.3](https://arxiv.org/html/2607.13683v2)

GEPA already uses reflective evolutionary optimization. Its current software supports component selection, objective frontiers and resource stopping criteria. Compare against the pinned version actually used, rather than treating contemporary GEPA as only a naive prompt rewrite. [Paper](https://arxiv.org/abs/2507.19457v2), [official API](https://gepa-ai.github.io/gepa/api/core/optimize/)

## Defensible contribution, conditional on results

An interpretable, resource-accounted comparison of **aggregate versus task-level retention gates**, and **one-, three-, and all-component edit limits**, on a shared local-agent runtime. The contribution would be the controlled evidence and reusable evaluation artifact, not a first-ever optimization primitive.

The strongest mechanistic question is whether a gate that forbids exchanging old successes for new ones meaningfully reduces **unseen-task** regressions, or instead mostly freezes progress on a reused development set. That outcome is unknown. Either answer can inform practice if measurements and limits are reported accurately.

Do not claim superiority to Self-Harness, HarnessFix, HarnessBank or GEPA from home-built look-alike baselines. A shared-runtime adaptation is a mechanism comparison, not a reproduction of those systems. A broader state-of-the-art claim requires an additional faithfully implemented/pinned baseline and an external benchmark.

## Remaining literature work before submission

- Inspect remaining screened papers' full evaluation protocols and exact code licenses.
- Repeat the search near submission: this review is a dated snapshot.
- Check whether later work already provides the same edit-budget ablation and task-retention comparison.
- Inspect HarnessOpt-Bench's actual benchmark/tool requirements before choosing an external subset.
- Verify final bibliography metadata from each pinned paper. Do not use a blog as evidence for a research organization's experimental protocol when its primary paper is available.

The supplied [Lil'Log article](https://lilianweng.github.io/posts/2026-07-04-harness/) was opened for context but is not used here to substantiate the proposal's specific “DeepMind double-blind evaluation” attribution.
