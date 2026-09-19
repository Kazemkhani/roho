# Run ROHO on free Kaggle, step by step

This guide runs a small **exploratory** local-model experiment, not the main study. No API key, paid inference endpoint, model training or billing setup is required. Kaggle GPU availability and quota depend on your account/current allocation; check the displayed allowance rather than assuming a fixed weekly number. See [Kaggle notebooks](https://www.kaggle.com/docs/notebooks) and [efficient GPU use](https://www.kaggle.com/docs/efficient-gpu-usage).

## 1. Get the private repository on your computer

```bash
gh auth login
gh repo clone Kazemkhani/roho
cd roho
python3 -m unittest discover -s tests -v
python3 scripts/package_source.py
```

If you already have the supplied local project, just open that directory and run the last two commands. Do not clone over an existing working directory. The ZIP appears at `dist/roho-source.zip`; the notebook is `notebooks/roho_kaggle.ipynb`.

You can also download the repository ZIP through GitHub while signed in, extract it locally, and run `python3 scripts/package_source.py` from the extracted directory. The packaging script includes an explicit source-file allowlist and excludes `.git`, credentials, caches, outputs and weights.

## 2. Upload source to a PRIVATE Kaggle dataset

1. Sign in to Kaggle.
2. Create a new dataset and upload **roho-source.zip**.
3. Keep the dataset **private**. Suggested name: `roho-private-source`.
4. Do not upload GitHub credentials, `.env`, your home directory, patient data or model weights.

This avoids using a personal access token in the notebook. Do not paste a GitHub token into a clone URL or publish it as a notebook output. A private repository does not automatically make your Kaggle notebook or dataset private—check both.

## 3. Create the notebook

1. Create a new private Kaggle notebook.
2. Import/upload `notebooks/roho_kaggle.ipynb` using the notebook import interface.
3. Add your private source dataset as an input.
4. In notebook settings, enable **Internet** and choose an available **GPU** accelerator. If these options are disabled, resolve the account verification/quota restriction shown by Kaggle. Do not pay for anything to bypass it.
5. Keep the notebook private.

The notebook locates `roho-source.zip` under `/kaggle/input` and extracts it into `/kaggle/working/roho`. It installs the small Python dependencies while retaining Kaggle's existing CUDA PyTorch. The Qwen weights are downloaded by the first real run. This uses storage/network time but no paid API.

## 4. Run the notebook cells in order

The supplied notebook performs:

1. Safe source extraction.
2. Dependency installation and CPU unit tests.
3. GPU availability check.
4. Real Qwen smoke optimization: five train + five dev tasks, A/C/D/E, one iteration and one proposal per learned arm.
5. Freeze, then the five-case pilot-test batch.
6. Descriptive report and output ZIP.

The default model is [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct). The adapter uses float16 on `cuda:0`, `trust_remote_code=False`, safe-tensor weights and no distributed training. Only one GPU is used; two assigned T4s do not automatically pool their memory. The driver resolves the model revision to a commit and writes it to `model.json`.

Do not install CPU-only PyTorch over the Kaggle image. If CUDA is false, stop and correct notebook settings. If a package install conflicts with an already imported library, restart the notebook session/kernel and rerun from the beginning before interpreting any results.

## 5. Equivalent commands inside Kaggle

After extraction and changing directory to `/kaggle/working/roho`, use notebook `!` commands:

```python
!python -m pip install -r requirements-kaggle.txt
!python -m unittest discover -s tests -v
!python -m roho doctor
!python -m roho run --config configs/kaggle-smoke.json --out /kaggle/working/roho-smoke
!python -m roho evaluate --out /kaggle/working/roho-smoke --confirm-frozen
!python -m roho report --out /kaggle/working/roho-smoke
```

The supplied notebook uses `subprocess.run(..., check=True)` instead, so later steps stop automatically if an earlier command fails.

## 6. Inspect before spending more quota

Open `/kaggle/working/roho-smoke/REPORT.md` and inspect:

- `model.json`: actual model commit, torch/Transformers versions, GPU, precision.
- `state.json`: source/config hashes, H0 scores, every proposal, acceptance reasons, final harnesses and optimization-token totals.
- `model_calls.jsonl`: metered classifier, proposer, solver and test calls.
- `episodes/`: per-task actions, tokens, timing and grader outcomes.
- `test_summary.json` and `test_outcomes.json`: final pilot-test measurements.

It is acceptable for no edit to pass. Zero solved baseline tasks makes regression undefined, not zero. Mostly invalid proposals indicate this model/setup may be inadequate. Do not report mock outputs, a five-task success increase, or shared-template pilot results as the paper's central evidence.

## 7. Run the larger exploratory pilot only if the smoke test is healthy

```python
!python -m roho run --config configs/kaggle-pilot.json --out /kaggle/working/roho-pilot
!python -m roho evaluate --out /kaggle/working/roho-pilot --confirm-frozen
!python -m roho report --out /kaggle/working/roho-pilot
```

This config uses 24 train, 12 dev, 24 test tasks, four arms, two rounds and two proposals per learned arm: up to 564 task episodes before skips. It uses different fixture seeds from the smoke run but still shares generator templates; it is not a template-independent generalization test. Measure smoke throughput before deciding whether the pilot fits the GPU time Kaggle displays.

Each learned arm has a common search-token ceiling. Realized usage may differ because invalid proposals consume slots without full evaluation. Diagnostic/proposal calls are charged. Search and final-test costs are separately labeled. A timeout is cooperative between turns, not a hard interrupt of an in-flight GPU operation.

## 8. Resume interrupted work

If the same output directory still exists:

```python
!python -m roho run --config configs/kaggle-pilot.json --out /kaggle/working/roho-pilot --resume
```

Completed task episodes are reused. Source, configuration, backend and model revision must match. Do not edit code/config and resume into the old results. If final evaluation was interrupted after freezing, rerun the same `evaluate --confirm-frozen` command; it completes missing cached episodes. A completed test batch is not rerun.

Kaggle working storage is not guaranteed to survive a session ending. Save/download a ZIP of the **entire output directory**, not just the report. To continue in a new session, add the saved output ZIP as another private dataset and restore it to the same `/kaggle/working/roho-pilot` path before resuming. Interrupted in-flight calls may not be fully metered; flag these runs in analysis.

## 9. Save results and stop the GPU

The notebook writes `/kaggle/working/roho-smoke-results.zip`. Download it from the notebook's output/file panel or save a private notebook version with outputs. For the larger run:

```python
import shutil
shutil.make_archive('/kaggle/working/roho-pilot-results', 'zip', '/kaggle/working/roho-pilot')
```

Turn off the active GPU session when finished. Do not schedule repeated GPU runs or use paid/cloud add-ons. Send the result ZIP back for analysis. The next decision is whether to upgrade the model or benchmark and run a properly frozen main experiment—not to manufacture a positive results section.

## Troubleshooting

| Symptom | Action |
|---|---|
| Private GitHub clone fails in Kaggle | Use the private source ZIP workflow; do not expose a token |
| `roho-source.zip` not found | Attach the private source dataset; inspect `/kaggle/input` |
| CUDA unavailable | Enable an available GPU; check account/quota requirements |
| Download fails | Check Internet access; restart only after preserving outputs |
| GPU out of memory | Restart to release other models; use smoke first; make any smaller-model/config change in a new output directory |
| Invalid JSON or no accepted changes | Inspect stored proposals; these are legitimate pilot failures |
| Source/config mismatch on resume | Restore the exact source/config used by that run; otherwise start a new run |
| `Context ceiling exceeded` | Inspect trace/prompt lengths; do not silently truncate the task or change a frozen main run |

GPU execution has not been validated by this assistant on your Kaggle account. The notebook is a prepared handoff; the exact validation sequence is steps 3–6 above.
