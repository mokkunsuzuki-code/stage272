#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_private_key(path: Path) -> Ed25519PrivateKey:
    pem = path.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(f"{path} is not an Ed25519 private key")
    return key


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a signed review checkpoint")
    parser.add_argument("--review-log", default="out/review_log/review_log.json")
    parser.add_argument("--review-log-hash", default="out/review_log/review_log_hash.txt")
    parser.add_argument("--history-dir", default="out/review_log_history")
    parser.add_argument("--private-key", default="keys/owner_private.pem")
    args = parser.parse_args()

    review_log_path = Path(args.review_log)
    review_log_hash_path = Path(args.review_log_hash)
    history_dir = Path(args.history_dir)
    private_key_path = Path(args.private_key)

    history_dir.mkdir(parents=True, exist_ok=True)

    if not review_log_path.exists():
        raise FileNotFoundError(f"review log not found: {review_log_path}")
    if not review_log_hash_path.exists():
        raise FileNotFoundError(f"review log hash not found: {review_log_hash_path}")

    review_log = json.loads(review_log_path.read_text(encoding="utf-8"))
    review_log_hash = review_log_hash_path.read_text(encoding="utf-8").strip()

    checkpoint_files = sorted(history_dir.glob("checkpoint_[0-9][0-9][0-9][0-9].json"))
    previous_checkpoint_hash = None
    previous_checkpoint_file = None
    checkpoint_id = 1

    if checkpoint_files:
        previous_checkpoint_file = checkpoint_files[-1]
        previous_payload = json.loads(previous_checkpoint_file.read_text(encoding="utf-8"))
        previous_checkpoint_hash = sha256_hex(canonical_json_bytes(previous_payload))
        checkpoint_id = int(previous_payload["checkpoint_id"]) + 1

    checkpoint_core = {
        "version": 1,
        "type": "review_log_checkpoint",
        "checkpoint_id": checkpoint_id,
        "timestamp": utc_now_iso(),
        "review_count": review_log["review_count"],
        "review_log_hash": review_log_hash,
        "merkle_root": review_log["merkle_root"],
        "previous_checkpoint_hash": previous_checkpoint_hash,
        "previous_checkpoint_file": previous_checkpoint_file.name if previous_checkpoint_file else None,
    }

    checkpoint_hash = sha256_hex(canonical_json_bytes(checkpoint_core))
    checkpoint_core["checkpoint_hash"] = checkpoint_hash

    private_key = load_private_key(private_key_path)
    signature = private_key.sign(checkpoint_hash.encode("utf-8"))
    checkpoint_core["signature"] = base64.b64encode(signature).decode("ascii")

    output_path = history_dir / f"checkpoint_{checkpoint_id:04d}.json"
    output_path.write_text(
        json.dumps(checkpoint_core, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    all_checkpoints = sorted(history_dir.glob("checkpoint_[0-9][0-9][0-9][0-9].json"))
    index_path = history_dir / "checkpoint_index.json"
    index_payload = {
        "version": 1,
        "latest_checkpoint_id": checkpoint_id,
        "latest_checkpoint_file": output_path.name,
        "checkpoint_count": len(all_checkpoints),
        "checkpoints": [p.name for p in all_checkpoints],
    }
    index_path.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("[OK] wrote:", output_path)
    print("[OK] wrote:", index_path)
    print("[OK] checkpoint_id:", checkpoint_id)
    print("[OK] checkpoint_hash:", checkpoint_hash)


if __name__ == "__main__":
    main()
