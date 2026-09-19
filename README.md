# ROHO — Kaggle-ready research pilot

Authors: Saksham Mishra and Amir Hossein Kazemkhani, University of Birmingham.

Prepared: 19 September 2026. Status: **executable exploratory pilot + prospective protocol v0.1**, not a completed paper, preregistration, or experimental finding. Author names and affiliation are user-supplied and require author confirmation before submission.

## Start here

Use [KAGGLE.md](KAGGLE.md) for the step-by-step free-Kaggle workflow. The repository is private; upload the source ZIP as a **private** Kaggle dataset instead of embedding a GitHub token in a notebook. Read [implementation limits](IMPLEMENTATION_STATUS.md) before treating a run as evidence.

```bash
git clone https://github.com/Kazemkhani/roho.git
cd roho
python -m unittest discover -s tests -v
python scripts/package_source.py
```

Clone requires your normal GitHub authentication. The generated `dist/roho-source.zip` contains source/configuration only, not credentials, Git metadata or model weights.

On Kaggle, after extracting the archive and enabling an available GPU and Internet:

```bash
python -m pip install -r requirements-kaggle.txt
python -m roho doctor
python -m roho run --config configs/kaggle-smoke.json --out /kaggle/working/roho-smoke
python -m roho evaluate --out /kaggle/working/roho-smoke --confirm-frozen
python -m roho report --out /kaggle/working/roho-smoke
```

The [notebook](notebooks/roho_kaggle.ipynb) automates these smoke-test steps. A maximum of 60 task episodes are scheduled by the smoke configuration before invalid-proposal skips; the larger pilot schedules up to 564. No runtime or success improvement is promised. Only the first GPU is used, even if Kaggle assigns two.

CPU-only software check (no model download):

```bash
python -m roho run --backend mock --config configs/kaggle-smoke.json --out runs/mock-smoke
python -m roho evaluate --out runs/mock-smoke --confirm-frozen
python -m roho report --out runs/mock-smoke
```

Mock outputs are explicitly labeled and are not research results.

## Recommended direction

**ROHO: Task-Level Regression Constraints for Budgeted Agent-Harness Optimization**

Research question: Under matched search budgets, how does explicitly retaining previously solved tasks change the success–cost trade-off of harness optimization, and how does a component edit budget affect that trade-off?

This is an empirical investigation of a particular combination and its trade-offs, not a claim to have invented failure-directed edits, regression gates, or multi-objective optimization. The closest literature already contains those ideas. “Regression-constrained” is more defensible than “regression-safe.”

The suggested study concerns local, frozen-model tool agents. It does not reuse the previous medical paper's experiments as evidence. Medical deployment and cross-model transfer are outside the first experiment.

## Read in this order

1. [Literature map](LITERATURE_MAP.md): 15 primary research sources, inspection depth, overlap, and novelty cautions.
2. [Experimental protocol](PROTOCOL.md): hypotheses, six arms, gates, splits, metrics, compute accounting, and analysis rules.
3. [Architecture](ARCHITECTURE.md): immutable boundaries, editable components, trace contract, and implementation sequence.
4. [Paper plan](PAPER_PLAN.md): the eventual eight-page manuscript and evidence needed to write it.
5. [Research log](RESEARCH_LOG.md): tools used and remaining checks.

## What is ready, and what is not

The research question, controlled contrasts, and implementation boundaries are specified. A bounded pilot benchmark, optimizer, model adapter and software tests are implemented. No real ROHO Qwen/Kaggle experiment has run yet. There are no measured LLM gains or publication-ready empirical conclusions.

Next action: run the supplied Kaggle smoke notebook, inspect its model-call and proposal logs, then decide whether the larger pilot is worthwhile. Qwen2.5-1.5B-Instruct is a small ungated starting model loaded from its official Hugging Face repository. Its resolved commit is recorded; this is not a claim that it is strong enough for the eventual paper.

Main-study model choice, runtime ceilings, independent templates and statistical repeat count remain feasibility-stage decisions. Freeze them and all dataset hashes before main experiments. The user requested a private GitHub repository; no arXiv or Zenodo publication is authorized by that request.
