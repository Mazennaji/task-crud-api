import json
from pathlib import Path

OUTPUT_DIR = Path("output")


def write_outputs(books: list[dict], errors: list[dict], report: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "books.json").write_text(json.dumps(books, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "errors.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "run-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")