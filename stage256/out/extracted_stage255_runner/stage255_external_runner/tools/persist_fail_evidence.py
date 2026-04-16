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


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_evidence_for_log(log_path: Path, output_dir: Path) -> dict:
    digest = sha256_file(log_path)
    raw = log_path.read_text(encoding="utf-8")
    line_count = len(raw.splitlines())

    evidence = {
        "version": 1,
        "type": "fail_evidence",
        "log_file": str(log_path.as_posix()),
        "sha256": digest,
        "size_bytes": log_path.stat().st_size,
        "line_count": line_count,
        "status": "unsigned",
    }

    evidence_name = log_path.stem + ".evidence.json"
    evidence_path = output_dir / evidence_name
    write_json(evidence_path, evidence)

    return {
        "log_file": str(log_path.as_posix()),
        "evidence_file": str(evidence_path.as_posix()),
        "sha256": digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist fail logs as hashed evidence.")
    parser.add_argument("--input-dir", required=True, help="Directory containing fail log files")
    parser.add_argument("--output-dir", required=True, help="Directory to write evidence JSON files")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise SystemExit(f"[ERROR] input directory not found: {input_dir}")

    log_files = sorted(input_dir.glob("*.log"))
    if not log_files:
        raise SystemExit(f"[ERROR] no .log files found in: {input_dir}")

    entries = []
    for log_path in log_files:
        entry = build_evidence_for_log(log_path, output_dir)
        entries.append(entry)
        print(f"[OK] evidence created: {entry['evidence_file']}")
        print(f"[OK] sha256: {entry['sha256']}")

    index = {
        "version": 1,
        "type": "fail_evidence_index",
        "entry_count": len(entries),
        "entries": entries,
    }

    index_path = output_dir / "index.json"
    write_json(index_path, index)
    print(f"[OK] wrote index: {index_path}")
    print(f"[OK] entry_count: {len(entries)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
