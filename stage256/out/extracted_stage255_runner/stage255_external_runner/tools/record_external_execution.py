#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer", required=True, help="Reviewer identifier")
    parser.add_argument("--anchor", required=True, help="Path to anchor_request.json")
    parser.add_argument("--manifest", required=True, help="Path to stage256 bundle manifest")
    parser.add_argument(
        "--log",
        default="out/external_execution_record/review_log.json",
        help="Path to review log JSON",
    )
    args = parser.parse_args()

    anchor_path = Path(args.anchor).resolve()
    manifest_path = Path(args.manifest).resolve()
    log_path = Path(args.log).resolve()

    if not anchor_path.exists():
        raise FileNotFoundError(f"Anchor not found: {anchor_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    anchor = load_json(anchor_path)

    qsp_result_rel = anchor["qsp_result_path"]
    qsp_result_path = manifest_path.parent / qsp_result_rel
    if not qsp_result_path.exists():
        raise FileNotFoundError(f"QSP result not found: {qsp_result_path}")

    out_dir = log_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    receipt = {
        "version": 1,
        "stage": "stage256",
        "type": "external_execution_receipt",
        "reviewer_id": args.reviewer,
        "executed_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "bundle_manifest_path": str(manifest_path),
        "bundle_manifest_sha256": sha256_file(manifest_path),
        "anchor_path": str(anchor_path),
        "anchor_sha256": sha256_file(anchor_path),
        "qsp_result_path": str(qsp_result_path),
        "qsp_result_sha256": sha256_file(qsp_result_path),
        "command_used": anchor.get("command_used", []),
    }

    receipt_sha256 = hashlib.sha256(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    receipt["receipt_sha256"] = receipt_sha256

    receipt_dir = out_dir / "receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    receipt_filename = f"{args.reviewer}_{receipt['executed_at_utc'].replace(':', '-')}.json"
    receipt_path = receipt_dir / receipt_filename
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if log_path.exists():
        review_log = load_json(log_path)
    else:
        review_log = {
            "version": 1,
            "stage": "stage256",
            "type": "external_execution_review_log",
            "records": [],
        }

    review_log["records"].append(
        {
            "reviewer_id": receipt["reviewer_id"],
            "executed_at_utc": receipt["executed_at_utc"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "anchor_sha256": receipt["anchor_sha256"],
            "qsp_result_sha256": receipt["qsp_result_sha256"],
            "receipt_path": str(receipt_path),
            "receipt_sha256": receipt["receipt_sha256"],
        }
    )

    log_path.write_text(
        json.dumps(review_log, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    log_sha_path = log_path.with_suffix(log_path.suffix + ".sha256")
    log_sha_path.write_text(
        f"{sha256_file(log_path)}  {log_path.name}\n",
        encoding="utf-8",
    )

    print(f"[OK] receipt created: {receipt_path}")
    print(f"[OK] review log updated: {log_path}")
    print(f"[OK] review log sha256: {sha256_file(log_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
