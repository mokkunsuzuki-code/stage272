#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify fail evidence hashes.")
    parser.add_argument("--index", required=True, help="Path to out/fail_evidence/index.json")
    args = parser.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        raise SystemExit(f"[ERROR] index not found: {index_path}")

    index = load_json(index_path)
    entries = index.get("entries", [])

    if not entries:
        raise SystemExit("[ERROR] no entries in fail evidence index")

    checked = 0
    for entry in entries:
        log_file = Path(entry["log_file"])
        expected = entry["sha256"]

        if not log_file.exists():
            raise SystemExit(f"[ERROR] log file missing: {log_file}")

        actual = sha256_file(log_file)
        if actual != expected:
            raise SystemExit(
                f"[ERROR] hash mismatch for {log_file}\n"
                f"expected: {expected}\n"
                f"actual:   {actual}"
            )

        print(f"[OK] verified: {log_file}")
        checked += 1

    print(f"[OK] all fail evidence verified ({checked} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
