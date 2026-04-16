#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import GitHub release anchor as normalized multi-anchor receipt")
    parser.add_argument("--request", required=True, help="Path to multi-anchor request JSON")
    parser.add_argument("--manifest", required=True, help="Stage250 release manifest path")
    parser.add_argument("--receipt", required=True, help="Stage250 GitHub release receipt path")
    parser.add_argument("--output", required=True, help="Output receipt JSON")
    args = parser.parse_args()

    request_path = Path(args.request)
    manifest_path = Path(args.manifest)
    receipt_path = Path(args.receipt)
    output_path = Path(args.output)

    request = json.loads(request_path.read_text(encoding="utf-8"))

    verify_script = Path("tools/verify_release_anchor.py")
    if not verify_script.exists():
        raise SystemExit("[ERROR] tools/verify_release_anchor.py not found (required from Stage250)")

    cmd = [
        sys.executable,
        str(verify_script),
        "--manifest",
        str(manifest_path),
        "--receipt",
        str(receipt_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("[ERROR] failed to verify Stage250 GitHub release anchor")

    normalized = {
        "version": 1,
        "anchor_type": "github_release_anchor",
        "subject_sha256": request["subject_sha256"],
        "source_manifest_path": str(manifest_path),
        "source_receipt_path": str(receipt_path),
        "imported_at_utc": utc_now(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[OK] imported GitHub receipt: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
