import copy
import difflib
from .common import canonical

H0 = {
    "system_prompt": "Complete the user's task using available tools. Be concise.",
    "tool_policy": "standard",
    "context_policy": "recent",
    "verification_policy": "none",
    "recovery_policy": 0,
    "memory_policy": "none",
}
OPTIONS = {
    "tool_policy": ["standard", "read_first", "calculate_first"],
    "context_policy": ["recent", "preserve_first"],
    "verification_policy": ["none", "artifact_exists"],
    "recovery_policy": [0, 1, 2],
    "memory_policy": ["none", "last_results"],
}
MASKS = {
    "tool_selection": ["tool_policy", "system_prompt"],
    "tool_argument": ["tool_policy", "recovery_policy"],
    "context": ["context_policy", "memory_policy"],
    "planning": ["system_prompt", "memory_policy", "tool_policy"],
    "verification": ["verification_policy", "system_prompt"],
    "recovery": ["recovery_policy", "context_policy"],
    "unknown": [],
}
ARMS = {
    "A": {"directed": False, "gate": "fixed", "budget": 0},
    "B": {"directed": False, "gate": "aggregate", "budget": 3},
    "C": {"directed": True, "gate": "aggregate", "budget": 3},
    "D": {"directed": True, "gate": "task", "budget": 3},
    "E": {"directed": True, "gate": "task", "budget": 1},
    "F": {"directed": True, "gate": "task", "budget": 6},
}


def apply_candidate(parent, proposal, arm, diagnosis, encode):
    if set(proposal) != {"changes", "hypothesis"}:
        raise ValueError("Proposal must have only changes and hypothesis")
    changes = proposal["changes"]
    if not isinstance(changes, dict) or not isinstance(proposal["hypothesis"], str):
        raise ValueError("Malformed proposal")
    if not changes or not set(changes) <= set(H0):
        raise ValueError("Empty changes or forbidden component")
    child = copy.deepcopy(parent)
    child.update(changes)
    if not isinstance(child["system_prompt"], str) or len(child["system_prompt"]) > 12000:
        raise ValueError("Invalid prompt")
    for component, allowed in OPTIONS.items():
        value = child[component]
        if type(value) is not type(allowed[0]) or value not in allowed:
            raise ValueError(f"Invalid {component}")
    actual = [k for k in H0 if child[k] != parent[k]]
    if not actual or len(actual) > ARMS[arm]["budget"]:
        raise ValueError("Empty diff or component budget exceeded")
    if ARMS[arm]["directed"] and not set(actual) <= set(MASKS.get(diagnosis, [])):
        raise ValueError("Failure-directed mask violated")
    total = 0
    for k in actual:
        old, new = encode(canonical(parent[k])), encode(canonical(child[k]))
        changed = sum((i2-i1)+(j2-j1) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if tag != "equal")
        if changed > 256:
            raise ValueError("Per-component token diff exceeded")
        total += changed
    if total > 1536 or len(encode(canonical(child))) > 4096:
        raise ValueError("Harness token budget exceeded")
    return child, actual


def summarize(records):
    if not records:
        raise ValueError("Cannot summarize empty evaluation")
    return {
        "n": len(records),
        "success": sum(r["success"] for r in records) / len(records),
        "mean_tokens": sum(r["input_tokens"] + r["output_tokens"] for r in records) / len(records),
    }


def lost_successes(parent, child):
    p = {r["task_id"]: r for r in parent}
    c = {r["task_id"]: r for r in child}
    if set(p) != set(c) or len(p) != len(parent) or len(c) != len(child):
        raise ValueError("Mismatched or duplicate task IDs")
    solved = sum(r["success"] for r in p.values())
    lost = sum(p[k]["success"] and not c[k]["success"] for k in p)
    return {"lost": lost, "previously_solved": solved, "rate": lost / solved if solved else None}


def eligible(parent_train, parent_dev, child_train, child_dev, baseline, gate):
    # Validate pairing even when only aggregate metrics determine promotion.
    lost_successes(parent_train, child_train)
    retention = lost_successes(parent_dev, child_dev)
    p, c = summarize(parent_train), summarize(child_train)
    if c["success"] < p["success"]:
        return False, "training_regression"
    if summarize(child_train + child_dev)["mean_tokens"] > 1.10 * summarize(baseline)["mean_tokens"]:
        return False, "cost_cap"
    if not (c["success"] > p["success"] or c["mean_tokens"] <= .95 * p["mean_tokens"]):
        return False, "no_training_improvement"
    if gate == "aggregate":
        ok = summarize(child_dev)["success"] >= summarize(parent_dev)["success"]
    elif gate == "task":
        ok = retention["previously_solved"] > 0 and retention["lost"] == 0
    else:
        raise ValueError("Unknown gate")
    return ok, "eligible" if ok else "development_gate"

