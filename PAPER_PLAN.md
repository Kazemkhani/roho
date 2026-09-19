# Eight-page manuscript plan

Provisional title: **ROHO: Task-Level Regression Constraints for Budgeted Agent-Harness Optimization**.

Saksham Mishra and Amir Hossein Kazemkhani — University of Birmingham.

The manuscript is empirical. It must not inherit a predetermined positive conclusion or a fixed theory/technology ratio from the previous medical-AI paper. An eight-page main-text target is an editorial choice, not a statement of arXiv's submission requirements; bibliography and reproducibility appendix can be separate.

| Approximate space | Content | Evidence required |
|---|---|---|
| 1 page | Abstract, problem, narrow contribution | Final endpoint estimates; no invented improvements |
| 1 page | Closest related work and overlap | Pinned Self-Harness, HarnessFix, HarnessBank, GEPA and benchmark sources |
| 1.5 pages | Gate definitions, edit budgets, immutable boundaries | Actual implementation; clear mathematical definitions |
| 1 page | Tasks, splits, model, seeds, compute controls | Frozen manifest and audited evaluator |
| 2 pages | Results and ablations | Task-level ledger; uncertainty; all prespecified arms |
| 1 page | Interpretation, negative outcomes, limitations | Scope-matched conclusions, overfitting and sample-size caveats |
| 0.5 page | Reproducibility and conclusion | Release manifest, exact commands and artifact hashes |

## Planned displays

- One architecture figure: proposer, trusted evaluator, gate, final-test boundary.
- One main table: test success, anchor regression counts/rate, input/output tokens, total search resources, latency.
- One paired gate comparison plot: D versus C with uncertainty and seed-level points.
- One edit-budget plot: E/D/F quality–regression–cost trade-offs.
- Optimization curves use train/dev only; do not repeatedly run the hidden test for prettier learning curves.

Do not present illustrative numbers as results. Include arm definitions and seed-level outcomes in the supplement. A method that accepts no edits remains an important outcome, not a missing run.

## Claims allowed only after evidence

- “Lower observed unseen-task regression” requires the prespecified paired test comparison.
- “More compute-efficient” requires both task-time costs and optimization costs; cheaper inference alone may not repay search.
- “Transferable” requires a separately frozen target-model test, with per-component interventions if causal attribution is claimed.
- “Regression-safe” or “guaranteed no forgetting” is not supported by this design.
- “Novel failure-directed mutation” is not supported by the literature review.

## LaTeX and release completion criteria

After analysis, write `paper/main.tex`, verified BibTeX entries, result tables generated directly from the ledger, and vector figures. Compile the PDF, check citations and cross-references, inspect every page, and verify that a clean source archive recompiles. Ship a README, pinned environment, benchmark definitions, split hashes, model identifiers, prompts, harness versions and raw machine-readable measurements.

This package is not yet an arXiv submission. Authors must review attribution, affiliation, model/data licenses, findings and limitations before any external upload. Repository publication, Zenodo deposition and arXiv submission are separate authorized actions; none have been performed.
