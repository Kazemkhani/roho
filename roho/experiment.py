"""Checkpointed PILOT orchestration. Final test is a separate CLI action."""
import copy
import importlib.metadata
import platform
from pathlib import Path
from .agent import episode
from .backend import BudgetExceeded, HFBackend, MockBackend
from .benchmark import make_tasks, dataset_hash
from .common import canonical, digest, parse_object, read_json, write_json
from .harness import H0, ARMS, MASKS, OPTIONS, apply_candidate, eligible, summarize, lost_successes


def source_hash():
    return digest({p.name: p.read_text() for p in sorted(Path(__file__).parent.glob("*.py"))})


def validate_config(config):
    if config.get("stage") != "exploratory_pilot":
        raise ValueError("This release supports exploratory pilots only, not the main study")
    for key in ("seed", "dataset_seed", "iterations", "candidates", "max_steps", "max_new_tokens", "max_context", "history_pairs", "task_seconds", "search_tokens_per_arm"):
        if type(config.get(key)) is not int or config[key] < 1:
            raise ValueError(f"Expected positive integer: {key}")
    if config["history_pairs"] < 2 or config["iterations"] > 5 or config["candidates"] > 3:
        raise ValueError("Pilot bounds exceeded")
    if len(set(config["arms"])) != len(config["arms"]) or "A" not in config["arms"] or not set(config["arms"]) <= set(ARMS):
        raise ValueError("Arms must be unique known arms including A")
    if set(config["tasks"]) != {"train", "dev", "test"} or any(type(n) is not int or not 1 <= n <= 120 for n in config["tasks"].values()):
        raise ValueError("Invalid task sizes")


def backend_for(root, config, kind):
    kwargs = {"budget": config["search_tokens_per_arm"]}
    if kind == "mock":
        return MockBackend(root, **kwargs)
    revision = config["revision"]
    if (root / "model.json").exists():
        revision = read_json(root / "model.json")["revision"]
    return HFBackend(root, config["model_id"], revision, config["max_context"], **kwargs)


def evaluate_tasks(root, namespace, harness, tasks, backend, config):
    harness_hash = digest(harness)
    rows = []
    for task in tasks:
        key = digest({"namespace": namespace, "harness": harness_hash, "task": task.task_id})
        path = root / "episodes" / (key + ".json")
        if path.exists():
            row = read_json(path)
        else:
            # Same task-time seed across candidate harnesses and arms.
            task_seed = int(digest([config["seed"], task.task_id])[:8], 16)
            row = episode(task, harness, backend, config, task_seed)
            row.update(namespace=namespace, harness_sha256=harness_hash, backend=backend.kind, attempt_seed=task_seed)
            write_json(path, row)
        rows.append(row)
    return rows


def training_evidence(tasks, rows):
    by_id = {t.task_id: t for t in tasks}
    failed = [r for r in rows if not r["success"]][:3]
    # No grader answers, fixture expectations, development traces or test cases.
    return [{"task_id": r["task_id"], "prompt": by_id[r["task_id"]].prompt, "termination_reason": r["termination_reason"], "events": canonical(r["events"][-4:])[:1800]} for r in failed]


def run(config_path, output, kind="hf", resume=False):
    config = read_json(config_path)
    validate_config(config)
    root = Path(output)
    state_path = root / "state.json"
    signature = digest({"config": config, "source": source_hash(), "backend": kind})
    if state_path.exists():
        if not resume:
            raise ValueError("Output already contains a run; use --resume or a fresh --out")
        state = read_json(state_path)
        if state["signature"] != signature:
            raise ValueError("Config/source/backend changed; cannot resume")
        if state["frozen"]:
            print("Optimization already frozen. Use evaluate for the final-test batch.")
            return
    else:
        if root.exists() and any(root.iterdir()):
            raise ValueError("Use an empty output directory")
        root.mkdir(parents=True, exist_ok=True)
        state = {"signature": signature, "source_hash": source_hash(), "config": config, "backend": kind, "arms": {}, "proposals": {}, "decisions": [], "frozen": False, "stage": "exploratory_pilot", "python": platform.python_version()}
        write_json(state_path, state)
    train = make_tasks("train", config["tasks"]["train"], config["dataset_seed"])
    dev = make_tasks("dev", config["tasks"]["dev"], config["dataset_seed"])
    state["dataset_hashes"] = {"train": dataset_hash(train), "dev": dataset_hash(dev)}
    backend = backend_for(root, config, kind)
    baseline_train = evaluate_tasks(root, "shared-baseline", H0, train, backend, config)
    baseline_dev = evaluate_tasks(root, "shared-baseline", H0, dev, backend, config)
    baseline = baseline_train + baseline_dev
    state["baseline"] = {"train": summarize(baseline_train), "dev": summarize(baseline_dev)}
    for arm in config["arms"]:
        progress = state["arms"].setdefault(arm, {"harness": copy.deepcopy(H0), "next_iteration": 0, "complete": arm == "A"})
        backend.scope = arm
        if progress["complete"]:
            continue
        for iteration in range(progress["next_iteration"], config["iterations"]):
            incumbent = progress["harness"]
            if incumbent == H0:
                parent_train, parent_dev = baseline_train, baseline_dev
            else:
                parent_train = evaluate_tasks(root, arm, incumbent, train, backend, config)
                parent_dev = evaluate_tasks(root, arm, incumbent, dev, backend, config)
            evidence = training_evidence(train, parent_train)
            qualified = []
            exhausted = False
            for slot in range(config["candidates"]):
                key = f"{arm}:{iteration}:{slot}"
                seed = config["seed"] + 1000 * iteration + slot
                try:
                    saved = state["proposals"].get(key)
                    if saved is None:
                        diagnosis = "unknown"
                        if ARMS[arm]["directed"]:
                            text, _ = backend.complete([
                                {"role": "system", "content": "ROHO_CLASSIFY: Classify these failed agent traces. Return only JSON with failure_class, one of " + canonical(list(MASKS))},
                                {"role": "user", "content": canonical(evidence)}
                            ], 96, seed)
                            try:
                                diagnosis = parse_object(text).get("failure_class", "unknown")
                                if diagnosis not in MASKS:
                                    diagnosis = "unknown"
                            except (ValueError, TypeError):
                                diagnosis = "unknown"
                        allowed = MASKS[diagnosis] if ARMS[arm]["directed"] else list(H0)
                        proposal_text, _ = backend.complete([
                            {"role": "system", "content": 'ROHO_PROPOSE: Improve an agent harness. Return only {"changes":{component:new_value},"hypothesis":"brief reason"}. Do not change unrelated components. No executable code. Valid policy values: ' + canonical(OPTIONS)},
                            {"role": "user", "content": canonical({"parent": incumbent, "failures": evidence, "allowed_components": allowed, "component_budget": ARMS[arm]["budget"], "proposal_slot": slot})}
                        ], 768, seed, temperature=.7)
                        saved = {"diagnosis": diagnosis, "text": proposal_text, "parent_hash": digest(incumbent)}
                        state["proposals"][key] = saved
                        write_json(state_path, state)
                    candidate, components = apply_candidate(incumbent, parse_object(saved["text"]), arm, saved["diagnosis"], backend.encode)
                    candidate_hash = digest(candidate)
                    earlier = [d for d in state["decisions"] if d["arm"] == arm and d["iteration"] == iteration and d["slot"] < slot]
                    if any(d.get("candidate_hash") == candidate_hash for d in earlier):
                        raise ValueError("Duplicate candidate consumes this proposal slot")
                    candidate_train = evaluate_tasks(root, arm, candidate, train, backend, config)
                    candidate_dev = evaluate_tasks(root, arm, candidate, dev, backend, config)
                    ok, reason = eligible(parent_train, parent_dev, candidate_train, candidate_dev, baseline, ARMS[arm]["gate"])
                    score = summarize(candidate_train)
                    decision = {"arm": arm, "iteration": iteration, "slot": slot, "candidate_hash": candidate_hash, "components": components, "eligible": ok, "reason": reason, "train": score, "dev": summarize(candidate_dev), "regression": lost_successes(parent_dev, candidate_dev)}
                    if ok:
                        qualified.append(((-score["success"], score["mean_tokens"], len(backend.encode(canonical(candidate))), candidate_hash), candidate))
                except BudgetExceeded as exc:
                    decision = {"arm": arm, "iteration": iteration, "slot": slot, "eligible": False, "reason": str(exc)}
                    exhausted = True
                except (ValueError, TypeError, KeyError) as exc:
                    decision = {"arm": arm, "iteration": iteration, "slot": slot, "eligible": False, "reason": "invalid_proposal: " + str(exc)}
                state["decisions"] = [d for d in state["decisions"] if (d["arm"], d["iteration"], d["slot"]) != (arm, iteration, slot)] + [decision]
                write_json(state_path, state)
                print(f"{key}: {decision['reason']}", flush=True)
                if exhausted:
                    break
            if qualified and not exhausted:
                progress["harness"] = sorted(qualified, key=lambda item: item[0])[0][1]
            progress["next_iteration"] = iteration + 1
            if exhausted:
                progress["stop_reason"] = "search_token_ceiling"
                break
            write_json(state_path, state)
        progress["complete"] = True
        write_json(state_path, state)
    state["frozen"] = True
    state["final_harness_hashes"] = {arm: digest(v["harness"]) for arm, v in state["arms"].items()}
    state["optimization_tokens_by_scope"] = backend.usage
    state["freeze_hash"] = digest({"signature": signature, "harnesses": state["final_harness_hashes"]})
    write_json(state_path, state)
    write_json(root / "environment.json", {"python": platform.python_version(), "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions() if d.metadata.get("Name")}})
    print("FROZEN. No test cases evaluated. Next: python -m roho evaluate --out", root, "--confirm-frozen")


def final_test(output, confirmed=False):
    if not confirmed:
        raise ValueError("Explicit --confirm-frozen is required to open the final pilot-test batch")
    root = Path(output)
    state = read_json(root / "state.json")
    if not state["frozen"] or state["source_hash"] != source_hash():
        raise ValueError("Run must be frozen under this exact source version")
    if digest({"config": state["config"], "source": source_hash(), "backend": state["backend"]}) != state["signature"]:
        raise ValueError("Frozen configuration/backend has changed")
    if {a: digest(v["harness"]) for a, v in state["arms"].items()} != state["final_harness_hashes"]:
        raise ValueError("Final harnesses have changed")
    if digest({"signature": state["signature"], "harnesses": state["final_harness_hashes"]}) != state["freeze_hash"]:
        raise ValueError("Freeze manifest has changed")
    if (root / "test_summary.json").exists():
        print("Final-test batch already complete. No rerun performed.")
        return
    config = state["config"]
    backend = backend_for(root, config, state["backend"])
    # A separate large reporting allowance; this is not optimization credit.
    backend.budget = 10**12
    tasks = make_tasks("test", config["tasks"]["test"], config["dataset_seed"])
    write_json(root / "test_opened.json", {"freeze_hash": state["freeze_hash"], "test_hash": dataset_hash(tasks), "status": "opened; do not tune against these outcomes"})
    outcomes = {}
    for arm in config["arms"]:
        backend.scope = "test-" + arm
        outcomes[arm] = evaluate_tasks(root, "test-" + arm, state["arms"][arm]["harness"], tasks, backend, config)
    summary = {"stage": "exploratory_pilot", "backend": backend.kind, "warning": "Shared-template synthetic pilot; not main-study evidence. Mock is software validation only.", "freeze_hash": state["freeze_hash"], "arms": {}}
    for arm, rows in outcomes.items():
        summary["arms"][arm] = {**summarize(rows), "anchor_regression": lost_successes(outcomes["A"], rows), "search_tokens": state["optimization_tokens_by_scope"].get(arm, 0)}
    write_json(root / "test_outcomes.json", outcomes)
    write_json(root / "test_summary.json", summary)
    print(canonical(summary))


def report(output):
    root = Path(output)
    state = read_json(root / "state.json")
    if not (root / "test_summary.json").exists():
        print("Optimization frozen:", state["frozen"], "— final test not complete.")
        print("Baseline:", canonical(state.get("baseline", {})))
        return
    summary = read_json(root / "test_summary.json")
    lines = ["# ROHO exploratory pilot", "", summary["warning"], "", "Backend: " + summary["backend"], "", "| Arm | Success | Lost / baseline solved | Mean tokens | Search tokens |", "|---|---:|---:|---:|---:|"]
    for arm, values in summary["arms"].items():
        regression = values["anchor_regression"]
        lines.append(f"| {arm} | {values['success']:.1%} | {regression['lost']} / {regression['previously_solved']} | {values['mean_tokens']:.1f} | {values['search_tokens']} |")
    lines.extend(["", "Search totals exclude the shared H0 evaluation, which is separately recorded in state.json and model_calls.jsonl. These one-seed descriptive pilot results have no inferential confidence intervals."])
    text = "\n".join(lines) + "\n"
    (root / "REPORT.md").write_text(text)
    print(text)
