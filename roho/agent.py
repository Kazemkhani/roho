import time
from .common import canonical, parse_object
from .tools import TOOL_DOCS, execute


def episode(task, harness, backend, config, seed):
    files = dict(task.files)
    tools = list(TOOL_DOCS)
    if harness["tool_policy"] == "read_first":
        tools.sort(key=lambda t: t != "read_file")
    elif harness["tool_policy"] == "calculate_first":
        tools.sort(key=lambda t: t != "calculate")
    system = (harness["system_prompt"] + '\nReturn exactly one JSON object per turn: {"tool":"name","args":{...}}. No prose or Markdown.\n' + "\n".join(f"{t}: {TOOL_DOCS[t]}" for t in tools))
    public = task.prompt + "\nAvailable virtual files: " + canonical(sorted(files))
    base = [{"role": "system", "content": system}, {"role": "user", "content": public}]
    history, events, results = [], [], []
    used_input = used_output = errors = 0
    answer, reason = "", "step_limit"
    started = time.monotonic()
    for step in range(config["max_steps"]):
        if time.monotonic() - started > config["task_seconds"]:
            reason = "time_limit"
            break
        keep = config["history_pairs"] * 2
        retained = history[-keep:]
        if harness["context_policy"] == "preserve_first" and len(history) > keep:
            retained = history[:2] + history[-(keep-2):]
        messages = base + retained
        if harness["memory_policy"] == "last_results" and results:
            messages = messages + [{"role": "user", "content": "Recent tool results: " + canonical(results[-2:])}]
        try:
            text, usage = backend.complete(messages, config["max_new_tokens"], seed + step)
        except ValueError as exc:
            reason = "context_or_input_error"
            events.append({"error": str(exc)})
            break
        used_input += usage["input_tokens"]
        used_output += usage["output_tokens"]
        try:
            call = parse_object(text)
            if set(call) != {"tool", "args"}:
                raise ValueError("Action must contain only tool and args")
            name, args = call["tool"], call["args"]
            if name == "finish":
                if not isinstance(args, dict) or set(args) != {"answer"} or not isinstance(args["answer"], (str, int)):
                    raise ValueError("finish requires scalar answer")
                if harness["verification_policy"] == "artifact_exists" and task.output_path and task.output_path not in files:
                    raise ValueError("Required output artifact is missing")
                answer, reason = str(args["answer"]), "finished"
                events.append({"tool": name, "args": args, "output": "finished"})
                break
            output = execute(name, args, files)
            results.append({"tool": name, "output": output})
            events.append({"tool": name, "args": args, "output": output})
        except (ValueError, TypeError, KeyError, SyntaxError) as exc:
            errors += 1
            output = "Tool/action error: " + str(exc)
            events.append({"raw": text[:2048], "error": str(exc)})
            if errors > harness["recovery_policy"]:
                reason = "tool_error"
                break
        history.extend([{"role": "assistant", "content": text}, {"role": "user", "content": str(output)[:4096]}])
    elapsed = time.monotonic() - started
    if elapsed > config["task_seconds"]:
        reason = "time_limit"
    return {"task_id": task.task_id, "family": task.family, "template_group": task.template_group, "success": reason == "finished" and task.grade(answer, files), "termination_reason": reason, "input_tokens": used_input, "output_tokens": used_output, "steps": len(events), "tool_errors": errors, "wall_seconds": elapsed, "events": events, "answer": answer}

