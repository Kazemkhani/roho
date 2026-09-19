"""Small transparent PILOT fixtures, not the proposed main benchmark.

Templates are public; hidden labels are not passed into model messages. Split
instances differ but share generator structure: do not claim template-OOD results.
"""
import json
import random
from dataclasses import asdict, dataclass
from .common import digest

FAMILIES = ("filesystem", "retrieval", "calculation", "table", "multitool")


@dataclass(frozen=True)
class Task:
    task_id: str
    family: str
    template_group: str
    prompt: str
    files: dict
    expected: str
    output_path: str | None = None

    def grade(self, answer, files):
        observed = files.get(self.output_path, "") if self.output_path else answer
        return str(observed).strip() == self.expected


def make_tasks(split, count, seed=20260919):
    if split not in ("train", "dev", "test") or count < 1:
        raise ValueError("Invalid split or count")
    rng = random.Random(f"roho-pilot-v1:{seed}:{split}")
    tasks = []
    for i in range(count):
        family = FAMILIES[i % len(FAMILIES)]
        a, b, c = [rng.randint(2, 40) for _ in range(3)]
        files, output_path = {}, None
        if family == "filesystem":
            word = rng.choice(["alpha", "bravo", "cider", "delta"]) + str(a)
            files = {"input.txt": word}
            prompt = "Read input.txt, convert its entire content to UPPERCASE, and write result.txt."
            expected, output_path = word.upper(), "result.txt"
        elif family == "retrieval":
            rows = [{"id": f"item-{j}", "value": rng.randint(10, 999)} for j in range(5)]
            target = rng.randrange(5)
            files = {"records.json": json.dumps(rows)}
            prompt = f"Find the value for id item-{target} in records.json. Finish with only that integer as answer."
            expected = str(rows[target]["value"])
        elif family == "calculation":
            prompt = f"Calculate ({a} + {b}) * {c}. Finish with only the integer as answer."
            expected = str((a + b) * c)
        elif family == "table":
            rows = [{"group": "A" if j % 2 else "B", "amount": rng.randint(1, 50)} for j in range(6)]
            files = {"table.json": json.dumps(rows)}
            prompt = "In table.json, sum amount only for rows whose group is A. Finish with only the integer as answer."
            expected = str(sum(row["amount"] for row in rows if row["group"] == "A"))
        else:
            files = {"numbers.json": json.dumps({"values": [a, b, c]})}
            prompt = "Read numbers.json, sum values, and write only the integer total into total.txt."
            expected, output_path = str(a + b + c), "total.txt"
        tasks.append(Task(f"{split}-{i:04}", family, family + "-pilot-v1", prompt, files, expected, output_path))
    return tasks


def dataset_hash(tasks):
    return digest([asdict(t) for t in tasks])

