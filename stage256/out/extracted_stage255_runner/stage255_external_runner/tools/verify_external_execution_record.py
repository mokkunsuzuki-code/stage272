#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
    parser.add_argument(
        "--log",
        default="out/external_execution_record/review_log.json",
        help="Path to review log JSON",
    )
    args = parser.parse_args()

    log_path = Path(args.log).resolve()
    if not log_path.exists():
        raise FileNotFoundError(f"Review log not found: {log_path}")

    review_log = load_json(log_path)
    records = review_log.get("records", [])

    for record in records:
        receipt_path = Path(record["receipt_path"])
        if not receipt_path.exists():
            raise FileNotFoundError(f"Receipt not found: {receipt_path}")

        receipt = load_json(receipt_path)

        actual_receipt_sha = hashlib.sha256(
            json.dumps(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"},
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        if actual_receipt_sha != receipt["receipt_sha256"]:
            raise ValueError(
                f"Receipt sha mismatch: {receipt_path} "
                f"expected={receipt['receipt_sha256']} actual={actual_receipt_sha}"
            )

        if actual_receipt_sha != record["receipt_sha256"]:
            raise ValueError(
                f"Review log receipt sha mismatch: {receipt_path} "
                f"expected={record['receipt_sha256']} actual={actual_receipt_sha}"
            )

        anchor_path = Path(receipt["anchor_path"])
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")
        if sha256_file(anchor_path) != receipt["anchor_sha256"]:
            raise ValueError(f"Anchor sha mismatch: {anchor_path}")

        manifest_path = Path(receipt["bundle_manifest_path"])
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        if sha256_file(manifest_path) != receipt["bundle_manifest_sha256"]:
            raise ValueError(f"Manifest sha mismatch: {manifest_path}")

        qsp_result_path = Path(receipt["qsp_result_path"])
        if not qsp_result_path.exists():
            raise FileNotFoundError(f"QSP result not found: {qsp_result_path}")
        if sha256_file(qsp_result_path) != receipt["qsp_result_sha256"]:
            raise ValueError(f"QSP result sha mismatch: {qsp_result_path}")

    log_sha_path = log_path.with_suffix(log_path.suffix + ".sha256")
    if log_sha_path.exists():
        expected_log_sha = log_sha_path.read_text(encoding="utf-8").strip().split()[0]
        actual_log_sha = sha256_file(log_path)
        if expected_log_sha != actual_log_sha:
            raise ValueError(
                f"Review log sha mismatch: expected={expected_log_sha} actual={actual_log_sha}"
            )

    print("[OK] all receipts verified")
    print("[OK] review log verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
