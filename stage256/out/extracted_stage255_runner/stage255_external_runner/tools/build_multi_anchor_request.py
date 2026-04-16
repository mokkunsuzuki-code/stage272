#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build multi-anchor request")
    parser.add_argument("--subject", required=True, help="Path to subject file")
    parser.add_argument("--output", required=True, help="Path to output request JSON")
    args = parser.parse_args()

    subject_path = Path(args.subject)
    output_path = Path(args.output)

    if not subject_path.exists():
        raise SystemExit(f"[ERROR] subject not found: {subject_path}")

    request = {
        "version": 1,
        "subject_path": str(subject_path),
        "subject_sha256": sha256_file(subject_path),
        "created_at_utc": utc_now(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[OK] wrote request: {output_path}")
    print(f"[OK] subject_sha256: {request['subject_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
