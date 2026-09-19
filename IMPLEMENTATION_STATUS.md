# What release 0.1 actually implements

This is an executable **exploratory pilot**, not a finished research study or faithful implementation of every proposed main-protocol feature.

Implemented: frozen Qwen Transformers adapter; mock software-test adapter; five virtual-tool task families; six configurable policies; diagnosis/proposal calls; enforced JSON diffs; component limits; aggregate/task-level gates; task-time token caps; metered proposal costs; per-arm token ceilings; episode checkpoints; source/config/model revision tracking; separate final-test opening; descriptive report; Kaggle walkthrough.

Important deviations from the prospective main protocol:

- The small public generator shares template structure across splits. Different fixture values/seeds do not constitute held-out template generalization. It is for feasibility only. The 60 independently authored template groups in PROTOCOL.md do not yet exist.
- Default runs use one optimization seed and one greedy task attempt. Outcome stability and power are not established. No confidence intervals or statistical superiority claims are produced.
- The runtime has a virtual-tool boundary, not a separate OS sandbox. Models never receive host tools or evaluator objects, and their output is not executed as Python. A malicious Python contributor/host process remains outside this threat model.
- Candidate patches change bounded text/configuration, not arbitrary harness source. This is a smaller search space than full harness engineering.
- Diagnosis is a single label in v0.1. Its masks allow at most three components, so F's nominal six-component ceiling adds no search space beyond D in this pilot. Do **not** run/report D-versus-F as an edit-budget experiment until multi-diagnosis union masks are implemented and frozen. Default configs exclude F.
- The 120-second task timeout is checked between turns and after generation; it is not a preemptive GPU watchdog. A running model call can overshoot. Crashes abort the run; they are not silently reclassified as successes.
- Input/output tokens count completed calls. An interrupted in-flight GPU call may have consumed resources without a completed ledger row. Resuming that task charges its new calls; completed episode caches remain usable. Record session interruptions and do not use interrupted pilot costs as exact main-study measurements.
- Actual Qwen/CUDA execution must be validated on Kaggle. Local mock tests do not validate GPU dependencies, performance or learning.

The small model is a low-resource starting point, not an assertion that it can reliably optimize harnesses. If proposals are mostly invalid, preserve that result. Do not replace them with hand-written repairs and call them model-generated improvement.

Before a main paper: audit evaluator/task difficulty; implement independent template groups, paired repeats, activation logging, the full main trace contract, preemptive limits, complete interrupted-call accounting and frozen statistical analysis. Pin all environment packages after the first verified Kaggle run. The model revision is resolved to a commit automatically and reused on resume, but Kaggle's base image still needs to be recorded/pinned where supported.

No software/data license has been chosen for public reuse. The repository is private. Authors should agree on licensing before a public release; model weights retain their own upstream terms.
