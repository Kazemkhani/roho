import contextlib
import copy
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from roho.agent import episode
from roho.backend import MockBackend, BudgetExceeded
from roho.benchmark import make_tasks, dataset_hash
from roho.common import canonical, read_json, write_json
from roho.experiment import run, final_test, report
from roho.harness import H0, apply_candidate, eligible, lost_successes
from roho.tools import calculate, execute, path_check

ROOT = Path(__file__).resolve().parents[1]


def records(values, tokens=100):
    return [{"task_id": str(i), "success": bool(v), "input_tokens": tokens, "output_tokens": 0} for i, v in enumerate(values)]


class ToolTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(calculate("(2+3)*7-1"), "34")

    def test_no_code_execution(self):
        for text in ("__import__('os').getcwd()", "2**100000", "2/3", "True+1", "10**2"):
            with self.assertRaises(ValueError):
                calculate(text)

    def test_arithmetic_bound(self):
        with self.assertRaises(ValueError):
            calculate("999999999999*999999999999")

    def test_paths(self):
        for path in ("/etc/passwd", "../secret", "a/../secret", "a\\b", "./x", ""):
            with self.assertRaises(ValueError):
                path_check(path)

    def test_virtual_write(self):
        files = {}
        execute("write_file", {"path": "x", "content": "ok"}, files)
        self.assertEqual(execute("read_file", {"path": "x"}, files), "ok")

    def test_unknown_tool_and_extra_args(self):
        for tool, args in (("shell", {"cmd": "pwd"}), ("read_file", {"path": "x", "extra": True})):
            with self.assertRaises(ValueError):
                execute(tool, args, {})


class BenchmarkTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(dataset_hash(make_tasks("train", 10)), dataset_hash(make_tasks("train", 10)))
        self.assertNotEqual(dataset_hash(make_tasks("train", 10)), dataset_hash(make_tasks("dev", 10)))

    def test_reference_solver(self):
        for split in ("train", "dev", "test"):
            for task in make_tasks(split, 30):
                files, answer = dict(task.files), ""
                if task.family == "filesystem":
                    files["result.txt"] = files["input.txt"].upper()
                elif task.family == "retrieval":
                    target = re.search(r"id (item-\d+)", task.prompt).group(1)
                    answer = str(next(r["value"] for r in json.loads(files["records.json"]) if r["id"] == target))
                elif task.family == "calculation":
                    a, b, c = map(int, re.findall(r"\d+", task.prompt))
                    answer = str((a + b) * c)
                elif task.family == "table":
                    answer = str(sum(r["amount"] for r in json.loads(files["table.json"]) if r["group"] == "A"))
                else:
                    files["total.txt"] = str(sum(json.loads(files["numbers.json"])["values"]))
                self.assertTrue(task.grade(answer, files), task.task_id)
                self.assertFalse(task.grade("wrong", {}))


class GateTests(unittest.TestCase):
    def test_aggregate_hides_losses(self):
        parent = records([1, 1, 0, 0])
        child = records([0, 1, 1, 1])
        train_parent, train_child = records([0, 0]), records([1, 0])
        self.assertTrue(eligible(train_parent, parent, train_child, child, train_parent + parent, "aggregate")[0])
        self.assertFalse(eligible(train_parent, parent, train_child, child, train_parent + parent, "task")[0])
        self.assertEqual(lost_successes(parent, child)["rate"], .5)

    def test_no_success_is_undefined(self):
        self.assertIsNone(lost_successes(records([0]), records([1]))["rate"])

    def test_missing_pairs(self):
        with self.assertRaises(ValueError):
            lost_successes(records([1]), records([1, 0]))

    def test_duplicate_ids(self):
        row = records([1])
        with self.assertRaises(ValueError):
            lost_successes(row + row, row)

    def test_no_change_rejected(self):
        rows = records([1, 0])
        self.assertFalse(eligible(rows, rows, rows, rows, rows, "task")[0])

    def test_cost_cap(self):
        old = records([0, 1])
        new = records([1, 1], 150)
        self.assertEqual(eligible(old, old, new, new, old, "aggregate")[1], "cost_cap")

    def test_cost_saving_can_pass(self):
        old, new = records([1, 0]), records([1, 0], 90)
        self.assertTrue(eligible(old, old, new, new, old, "task")[0])


class CandidateTests(unittest.TestCase):
    def apply(self, changes, arm="E", diagnosis="verification"):
        return apply_candidate(H0, {"changes": changes, "hypothesis": "test"}, arm, diagnosis, lambda s: list(s.encode()))

    def test_valid(self):
        child, keys = self.apply({"verification_policy": "artifact_exists"})
        self.assertEqual(keys, ["verification_policy"])
        self.assertEqual(H0["verification_policy"], "none")

    def test_forbidden_evaluator(self):
        with self.assertRaises(ValueError):
            self.apply({"evaluator": "pass"})

    def test_component_budget(self):
        with self.assertRaises(ValueError):
            self.apply({"verification_policy": "artifact_exists", "system_prompt": "changed"})

    def test_mask(self):
        with self.assertRaises(ValueError):
            self.apply({"context_policy": "preserve_first"})

    def test_noop(self):
        with self.assertRaises(ValueError):
            self.apply({"system_prompt": H0["system_prompt"]})

    def test_invalid_enum_and_bool(self):
        for changes in ({"recovery_policy": True}, {"verification_policy": "eval"}):
            with self.assertRaises(ValueError):
                self.apply(changes)

    def test_large_edit(self):
        with self.assertRaises(ValueError):
            self.apply({"system_prompt": "x" * 1000})


class RuntimeTests(unittest.TestCase):
    def test_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            backend = MockBackend(temp, budget=1)
            with self.assertRaises(BudgetExceeded):
                backend.complete([{"role": "user", "content": "hello"}], 10, 1)

    def test_empty_answer_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            config = read_json(ROOT / "configs/kaggle-smoke.json")
            row = episode(make_tasks("train", 1)[0], H0, MockBackend(temp), config, 1)
            self.assertFalse(row["success"])
            self.assertGreater(row["input_tokens"], 0)

    def test_end_to_end_checkpoint_and_freeze(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            output = Path(temp) / "run"
            config = ROOT / "configs/kaggle-smoke.json"
            run(config, output, "mock")
            state = read_json(output / "state.json")
            self.assertTrue(state["frozen"])
            self.assertFalse((output / "test_outcomes.json").exists())
            self.assertEqual(set(state["arms"]), {"A", "C", "D", "E"})
            with self.assertRaises(ValueError):
                run(config, output, "mock")
            run(config, output, "mock", True)
            with self.assertRaises(ValueError):
                final_test(output)
            final_test(output, True)
            calls = (output / "model_calls.jsonl").read_text()
            final_test(output, True)
            self.assertEqual(calls, (output / "model_calls.jsonl").read_text())
            report(output)
            self.assertIn("mock-software-test-only", (output / "REPORT.md").read_text())
            summary = read_json(output / "test_summary.json")
            self.assertTrue(all(v["anchor_regression"]["rate"] is None for v in summary["arms"].values()))


if __name__ == "__main__":
    unittest.main()

