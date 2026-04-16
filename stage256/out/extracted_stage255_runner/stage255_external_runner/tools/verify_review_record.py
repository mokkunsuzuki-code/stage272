#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ALLOWED_VERDICTS = {"observed", "reproduced", "reviewed", "approved"}
REQUIRED_FIELDS = {
    "version",
    "review_id",
    "reviewer_id",
    "review_date",
    "repository",
    "reviewed_commit",
    "scope_document",
    "reviewed_artifacts",
    "verdict",
    "notes",
    "acknowledgment"
}

def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Stage244 review record")
    parser.add_argument("--input", required=True, help="Path to review record JSON")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        fail(f"input file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        fail(f"missing required fields: {sorted(missing)}")

    if data["version"] != 1:
        fail("version must be 1")

    if not isinstance(data["reviewed_artifacts"], list) or not data["reviewed_artifacts"]:
        fail("reviewed_artifacts must be a non-empty list")

    if data["verdict"] not in ALLOWED_VERDICTS:
        fail(f"invalid verdict: {data['verdict']}")

    acknowledgment = data["acknowledgment"]
    if not isinstance(acknowledgment, dict):
        fail("acknowledgment must be an object")

    if "type" not in acknowledgment or "reference" not in acknowledgment:
        fail("acknowledgment must contain 'type' and 'reference'")

    print("[OK] review record is valid")

if __name__ == "__main__":
    main()
