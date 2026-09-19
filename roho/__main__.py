import argparse
import importlib.util
import platform
from .experiment import run, final_test, report


def main():
    parser = argparse.ArgumentParser(description="ROHO exploratory Kaggle pilot")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    command = sub.add_parser("run")
    command.add_argument("--config", required=True)
    command.add_argument("--out", required=True)
    command.add_argument("--backend", choices=["hf", "mock"], default="hf")
    command.add_argument("--resume", action="store_true")
    command = sub.add_parser("evaluate")
    command.add_argument("--out", required=True)
    command.add_argument("--confirm-frozen", action="store_true")
    command = sub.add_parser("report")
    command.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "doctor":
        print("Python:", platform.python_version())
        for name in ("torch", "transformers", "huggingface_hub"):
            print(name, "installed" if importlib.util.find_spec(name) else "MISSING")
        if importlib.util.find_spec("torch"):
            import torch
            print("CUDA:", torch.cuda.is_available())
            if torch.cuda.is_available():
                print("GPU:", torch.cuda.get_device_name(0))
    elif args.command == "run":
        run(args.config, args.out, args.backend, args.resume)
    elif args.command == "evaluate":
        final_test(args.out, args.confirm_frozen)
    else:
        report(args.out)


if __name__ == "__main__":
    main()

