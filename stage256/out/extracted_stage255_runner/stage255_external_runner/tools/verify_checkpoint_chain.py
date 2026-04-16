#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_public_key(path: Path) -> Ed25519PublicKey:
    pem = path.read_bytes()
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError(f"{path} is not an Ed25519 public key")
    return key


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify review checkpoint chain")
    parser.add_argument("--history-dir", default="out/review_log_history")
    parser.add_argument("--public-key", default="keys/owner_public.pem")
    args = parser.parse_args()

    history_dir = Path(args.history_dir)
    public_key_path = Path(args.public_key)

    checkpoint_files = sorted(history_dir.glob("checkpoint_[0-9][0-9][0-9][0-9].json"))
    if not checkpoint_files:
        raise FileNotFoundError(f"no checkpoints found in {history_dir}")

    public_key = load_public_key(public_key_path)
    previous_hash = None
    previous_name = None

    for checkpoint_file in checkpoint_files:
        payload = json.loads(checkpoint_file.read_text(encoding="utf-8"))

        signature_b64 = payload.get("signature")
        if signature_b64 is None:
            raise RuntimeError(f"missing signature in {checkpoint_file.name}")

        core = {k: v for k, v in payload.items() if k != "signature"}
        stored_checkpoint_hash = core["checkpoint_hash"]

        recomputed_checkpoint_hash = sha256_hex(
            canonical_json_bytes({k: v for k, v in core.items() if k != "checkpoint_hash"})
        )
        if recomputed_checkpoint_hash != stored_checkpoint_hash:
            raise RuntimeError(f"checkpoint hash mismatch in {checkpoint_file.name}")

        if core["previous_checkpoint_hash"] != previous_hash:
            raise RuntimeError(f"previous hash mismatch in {checkpoint_file.name}")

        if core["previous_checkpoint_file"] != previous_name:
            raise RuntimeError(f"previous file mismatch in {checkpoint_file.name}")

        try:
            public_key.verify(
                base64.b64decode(signature_b64),
                stored_checkpoint_hash.encode("utf-8"),
            )
        except InvalidSignature as exc:
            raise RuntimeError(f"signature verification failed in {checkpoint_file.name}") from exc

        previous_hash = sha256_hex(canonical_json_bytes(payload))
        previous_name = checkpoint_file.name

        print("[OK] verified:", checkpoint_file.name)

    index_path = history_dir / "checkpoint_index.json"
    if index_path.exists():
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        latest_payload = json.loads(checkpoint_files[-1].read_text(encoding="utf-8"))

        if index_payload["latest_checkpoint_file"] != checkpoint_files[-1].name:
            raise RuntimeError("checkpoint_index latest_checkpoint_file mismatch")

        if index_payload["latest_checkpoint_id"] != latest_payload["checkpoint_id"]:
            raise RuntimeError("checkpoint_index latest_checkpoint_id mismatch")

    print("[OK] chain_length:", len(checkpoint_files))
    print("[OK] checkpoint_chain_verified: True")


if __name__ == "__main__":
    main()
