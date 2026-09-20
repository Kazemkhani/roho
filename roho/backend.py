import json
import time
from pathlib import Path
from .common import canonical, write_json


class BudgetExceeded(RuntimeError):
    pass


class Backend:
    """Each model call is durably metered; no completed-call reuse on resume."""
    def __init__(self, root, scope="baseline", budget=1000000):
        self.root = Path(root)
        self.scope = scope
        self.budget = budget
        self.path = self.root / "model_calls.jsonl"
        self.usage = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                row = json.loads(line)
                self.usage[row["scope"]] = self.usage.get(row["scope"], 0) + row["input_tokens"] + row["output_tokens"]

    def complete(self, messages, max_new_tokens, seed, temperature=0):
        input_tokens = self.input_length(messages)
        if self.usage.get(self.scope, 0) + input_tokens + max_new_tokens > self.budget:
            raise BudgetExceeded(f"Search-token ceiling reached for {self.scope}")
        started = time.monotonic()
        text, output_tokens = self.generate(messages, max_new_tokens, seed, temperature)
        elapsed = time.monotonic() - started
        row = {"scope": self.scope, "input_tokens": input_tokens, "output_tokens": output_tokens, "seconds": elapsed, "seed": seed, "temperature": temperature, "backend": self.kind}
        self.usage[self.scope] = self.usage.get(self.scope, 0) + input_tokens + output_tokens
        with self.path.open("a") as stream:
            stream.write(canonical(row) + "\n")
            stream.flush()
        return text, row


class MockBackend(Backend):
    kind = "mock-software-test-only"
    def encode(self, text):
        return list(text.encode())

    def input_length(self, messages):
        return len(self.encode(canonical(messages)))

    def generate(self, messages, max_new_tokens, seed, temperature):
        instruction = messages[0]["content"]
        if "ROHO_CLASSIFY" in instruction:
            text = '{"failure_class":"verification"}'
        elif "ROHO_PROPOSE" in instruction:
            text = '{"changes":{"system_prompt":"Check available evidence before answering."},"hypothesis":"software-test placeholder"}'
        else:
            text = '{"tool":"finish","args":{"answer":"0"}}'
        return text, min(len(self.encode(text)), max_new_tokens)


class HFBackend(Backend):
    kind = "huggingface-local"
    def __init__(self, root, model_id, revision, max_context, **kwargs):
        super().__init__(root, **kwargs)
        import torch
        import transformers
        from huggingface_hub import model_info
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU required for this Kaggle adapter. Enable Accelerator; use --backend mock for CPU tests.")
        self.torch = torch
        self.max_context = max_context
        # Resolve mutable branch once; all downloads use the resulting commit.
        self.revision = model_info(model_id, revision=revision).sha
        metadata_path = self.root / "model.json"
        if metadata_path.exists():
            old = json.loads(metadata_path.read_text())
            if old["revision"] != self.revision or old["model_id"] != model_id:
                raise ValueError("Model revision changed; resume requires recorded commit")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=self.revision, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, revision=self.revision, dtype=torch.float32, trust_remote_code=False, use_safetensors=True, attn_implementation="eager").to("cuda:0").eval()
        write_json(metadata_path, {"model_id": model_id, "revision": self.revision, "dtype": "float32", "torch": torch.__version__, "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(0), "device": "cuda:0", "max_context": max_context})

    def encode(self, text):
        return self.tokenizer.encode(text, add_special_tokens=False)

    def tokens(self, messages):
        return self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)

    def input_length(self, messages):
        return len(self.tokens(messages))

    def generate(self, messages, max_new_tokens, seed, temperature):
        torch = self.torch
        from transformers import set_seed
        set_seed(seed)
        ids = self.tokens(messages)
        if len(ids) + max_new_tokens > self.max_context:
            raise ValueError("Context ceiling exceeded; no silent task truncation")
        inputs = torch.tensor([ids], device="cuda:0")
        kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.eos_token_id,
            "remove_invalid_values": True,
            "renormalize_logits": True,
        }
        if temperature > 0:
            kwargs.update(temperature=temperature, top_p=.9)
        with torch.inference_mode():
            output = self.model.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs), **kwargs)
        continuation = output[0, len(ids):]
        return self.tokenizer.decode(continuation, skip_special_tokens=True), len(continuation)
