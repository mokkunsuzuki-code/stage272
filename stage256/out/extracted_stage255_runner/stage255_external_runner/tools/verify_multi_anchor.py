#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_checkpoint_sha256(checkpoint_path: Path) -> str:
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    raw = json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_local_witness(receipt: dict, subject_sha256: str) -> bool:
    if receipt.get("subject_sha256") != subject_sha256:
        return False
    public_key_path = Path(receipt["public_key_path"])
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    signature = base64.b64decode(receipt["signature_base64"])
    public_key.verify(signature, subject_sha256.encode("utf-8"))
    return True


def verify_checkpoint_witness(receipt: dict, subject_sha256: str) -> bool:
    if receipt.get("subject_sha256") != subject_sha256:
        return False
    checkpoint_path = Path(receipt["checkpoint_path"])
    if not checkpoint_path.exists():
        return False
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("subject_sha256") != subject_sha256:
        return False
    recomputed = canonical_checkpoint_sha256(checkpoint_path)
    if recomputed != receipt.get("checkpoint_sha256"):
        return False
    public_key_path = Path(receipt["public_key_path"])
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    signature = base64.b64decode(receipt["signature_base64"])
    public_key.verify(signature, recomputed.encode("utf-8"))
    return True


def verify_github_anchor(receipt: dict, subject_sha256: str) -> bool:
    if receipt.get("subject_sha256") != subject_sha256:
        return False

    manifest_path = Path(receipt["source_manifest_path"])
    source_receipt_path = Path(receipt["source_receipt_path"])

    if sha256_file(manifest_path) != subject_sha256:
        return False

    verify_script = Path("tools/verify_release_anchor.py")
    if not verify_script.exists():
        return False

    cmd = [
        sys.executable,
        str(verify_script),
        "--manifest",
        str(manifest_path),
        "--receipt",
        str(source_receipt_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify multi-anchor receipts with threshold policy")
    parser.add_argument("--request", required=True, help="Path to request JSON")
    parser.add_argument("--policy", required=True, help="Path to policy JSON")
    parser.add_argument("--receipts", nargs="+", required=True, help="Receipt JSON paths")
    args = parser.parse_args()

    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))

    subject_sha256 = request["subject_sha256"]
    accepted_types = set(policy["accepted_anchor_types"])
    threshold = int(policy["threshold"])

    valid_anchor_types: list[str] = []

    for receipt_path_str in args.receipts:
        receipt_path = Path(receipt_path_str)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        anchor_type = receipt.get("anchor_type")

        if anchor_type not in accepted_types:
            print(f"[SKIP] {receipt_path} unsupported anchor_type={anchor_type}")
            continue

        try:
            if anchor_type == "local_witness":
                ok = verify_local_witness(receipt, subject_sha256)
            elif anchor_type == "checkpoint_witness":
                ok = verify_checkpoint_witness(receipt, subject_sha256)
            elif anchor_type == "github_release_anchor":
                ok = verify_github_anchor(receipt, subject_sha256)
            else:
                ok = False
        except Exception as exc:
            print(f"[FAIL] {receipt_path} anchor_type={anchor_type} error={exc}")
            ok = False

        if ok:
            print(f"[OK] {receipt_path} anchor_type={anchor_type}")
            if anchor_type not in valid_anchor_types:
                valid_anchor_types.append(anchor_type)
        else:
            print(f"[FAIL] {receipt_path} anchor_type={anchor_type}")

    print(f"[INFO] valid distinct anchors: {len(valid_anchor_types)} / threshold {threshold}")
    print(f"[INFO] valid anchor types: {', '.join(valid_anchor_types) if valid_anchor_types else '(none)'}")

    if len(valid_anchor_types) >= threshold:
        print("[OK] multi-anchor verification passed")
        return 0

    print("[ERROR] multi-anchor verification failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
