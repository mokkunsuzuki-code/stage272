#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def next_index(checkpoint_dir: Path) -> int:
    existing = sorted(checkpoint_dir.glob("checkpoint_*.json"))
    if not existing:
        return 1
    last = existing[-1].stem.split("_")[-1]
    return int(last) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build checkpoint witness anchor")
    parser.add_argument("--request", required=True, help="Path to multi-anchor request JSON")
    parser.add_argument("--private-key", required=True, help="Ed25519 private key PEM")
    parser.add_argument("--key-id", required=True, help="Logical key id")
    parser.add_argument("--checkpoint-dir", required=True, help="Directory for checkpoint history")
    parser.add_argument("--output", required=True, help="Output receipt JSON")
    args = parser.parse_args()

    request_path = Path(args.request)
    private_key_path = Path(args.private_key)
    checkpoint_dir = Path(args.checkpoint_dir)
    output_path = Path(args.output)

    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    request = json.loads(request_path.read_text(encoding="utf-8"))
    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)

    idx = next_index(checkpoint_dir)
    previous_path = checkpoint_dir / f"checkpoint_{idx - 1:04d}.json"
    previous_sha256 = sha256_file(previous_path) if previous_path.exists() else None

    checkpoint = {
        "version": 1,
        "index": idx,
        "previous_checkpoint_sha256": previous_sha256,
        "subject_sha256": request["subject_sha256"],
        "created_at_utc": utc_now(),
    }

    checkpoint_bytes = canonical_bytes(checkpoint)
    checkpoint_sha256 = sha256_bytes(checkpoint_bytes)
    signature = private_key.sign(checkpoint_sha256.encode("utf-8"))

    checkpoint_path = checkpoint_dir / f"checkpoint_{idx:04d}.json"
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    receipt = {
        "version": 1,
        "anchor_type": "checkpoint_witness",
        "key_id": args.key_id,
        "public_key_path": str(private_key_path.with_name(private_key_path.name.replace("_private.pem", "_public.pem"))),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_sha256,
        "subject_sha256": request["subject_sha256"],
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[OK] wrote checkpoint: {checkpoint_path}")
    print(f"[OK] wrote checkpoint receipt: {output_path}")
    print(f"[OK] checkpoint_sha256: {checkpoint_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
