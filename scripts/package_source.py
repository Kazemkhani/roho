"""Create a credential-free source ZIP suitable for a PRIVATE Kaggle dataset."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("roho", "tests", "configs", "scripts", "notebooks", ".github")
FILES = ("README.md", "KAGGLE.md", "IMPLEMENTATION_STATUS.md", "LITERATURE_MAP.md", "PROTOCOL.md", "ARCHITECTURE.md", "PAPER_PLAN.md", "RESEARCH_LOG.md", "pyproject.toml", "requirements-kaggle.txt", ".gitignore")


def main():
    destination = ROOT / "dist" / "roho-source.zip"
    destination.parent.mkdir(exist_ok=True)
    paths = [ROOT / name for name in FILES]
    for name in DIRECTORIES:
        paths.extend(p for p in (ROOT / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            if path.is_file():
                archive.write(path, "roho/" + str(path.relative_to(ROOT)))
    print(destination)


if __name__ == "__main__":
    main()

