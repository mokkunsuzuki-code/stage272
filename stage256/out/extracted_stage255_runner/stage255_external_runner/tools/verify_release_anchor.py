#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Motohiro Suzuki

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Stage250 release anchor receipt")
    parser.add_argument(
        "--manifest",
        default="out/release_anchor/release_manifest.json",
        help="Path to release manifest JSON",
    )
    parser.add_argument(
        "--receipt",
        default="out/release_anchor/github_release_anchor_receipt.json",
        help="Path to release anchor receipt JSON",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    receipt_path = Path(args.receipt)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest file: {manifest_path}")
    if not receipt_path.exists():
        raise FileNotFoundError(f"Missing receipt file: {receipt_path}")

    manifest = read_json(manifest_path)
    receipt = read_json(receipt_path)

    manifest_sha256 = sha256_file(manifest_path)
    if manifest_sha256 != receipt.get("manifest_sha256"):
        raise ValueError("Manifest SHA256 mismatch between manifest and receipt")

    if manifest.get("stage") != "stage250":
        raise ValueError("Manifest stage is not stage250")

    if receipt.get("stage") != "stage250":
        raise ValueError("Receipt stage is not stage250")

    if receipt.get("release_anchor_type") != "github_release_anchor_receipt":
        raise ValueError("Unexpected receipt release_anchor_type")

    if manifest.get("release_tag") != receipt.get("release_tag"):
        raise ValueError("Release tag mismatch between manifest and receipt")

    manifest_binding = manifest.get("semantic_binding", {})
    if manifest_binding.get("request_sequence") != receipt.get("request_sequence"):
        raise ValueError("Request sequence mismatch")

    if manifest_binding.get("checkpoint_id") != receipt.get("checkpoint_id"):
        raise ValueError("Checkpoint ID mismatch")

    if manifest_binding.get("checkpoint_sequence") != receipt.get("checkpoint_sequence"):
        raise ValueError("Checkpoint sequence mismatch")

    if manifest_binding.get("request_sha256") != receipt.get("request_sha256"):
        raise ValueError("Request SHA256 mismatch")

    run_url = receipt.get("run_url")
    if not run_url or "/actions/runs/" not in run_url:
        raise ValueError("Receipt run_url is missing or malformed")

    print("[OK] release anchor verified")
    print(f"[OK] manifest_sha256: {manifest_sha256}")
    print(f"[OK] release_tag: {manifest.get('release_tag')}")
    print(f"[OK] checkpoint_id: {manifest_binding.get('checkpoint_id')}")
    print(f"[OK] request_sha256: {manifest_binding.get('request_sha256')}")
    print(f"[OK] run_url: {run_url}")


if __name__ == "__main__":
    main()
