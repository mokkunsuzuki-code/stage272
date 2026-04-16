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


def merkle_root_from_leaves(leaf_hashes: list[str]) -> str:
    if not leaf_hashes:
        return sha256_hex(b"")

    level = leaf_hashes[:]
    while len(level) > 1:
        next_level: list[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            parent = sha256_hex(bytes.fromhex(left) + bytes.fromhex(right))
            next_level.append(parent)
        level = next_level
    return level[0]


def load_public_key(path: Path) -> Ed25519PublicKey:
    pem = path.read_bytes()
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError(f"{path} is not an Ed25519 public key")
    return key


def verify_review_log(review_log_path: Path, hash_path: Path, sig_path: Path, public_key_path: Path) -> dict[str, Any]:
    review_log = json.loads(review_log_path.read_text(encoding="utf-8"))
    expected_hash = hash_path.read_text(encoding="utf-8").strip()
    signature = base64.b64decode(sig_path.read_text(encoding="utf-8").strip())

    actual_hash = sha256_hex(canonical_json_bytes(review_log))
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"review_log hash mismatch: expected {expected_hash}, got {actual_hash}"
        )

    entries = review_log.get("entries", [])
    leaf_hash_index = review_log.get("leaf_hashes", [])
    stored_merkle_root = review_log.get("merkle_root")

    if len(entries) != len(leaf_hash_index):
        raise RuntimeError("entry count and leaf_hashes count do not match")

    recomputed_leaf_hashes: list[str] = []
    for idx, entry in enumerate(entries):
        recomputed = sha256_hex(canonical_json_bytes(entry))
        indexed = leaf_hash_index[idx].get("leaf_hash")
        if recomputed != indexed:
            raise RuntimeError(
                f"leaf hash mismatch at index {idx}: expected {indexed}, got {recomputed}"
            )
        recomputed_leaf_hashes.append(recomputed)

    recomputed_merkle_root = merkle_root_from_leaves(recomputed_leaf_hashes)
    if recomputed_merkle_root != stored_merkle_root:
        raise RuntimeError(
            f"merkle root mismatch: expected {stored_merkle_root}, got {recomputed_merkle_root}"
        )

    public_key = load_public_key(public_key_path)
    try:
        public_key.verify(signature, expected_hash.encode("utf-8"))
    except InvalidSignature as exc:
        raise RuntimeError("review_log signature verification failed") from exc

    return {
        "review_count": len(entries),
        "review_log_hash": expected_hash,
        "merkle_root": recomputed_merkle_root,
        "signature_verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify signed review transparency log")
    parser.add_argument("--review-log", default="out/review_log/review_log.json")
    parser.add_argument("--hash-file", default="out/review_log/review_log_hash.txt")
    parser.add_argument("--sig-file", default="out/review_log/review_log.sig")
    parser.add_argument("--public-key", default="keys/owner_public.pem")
    args = parser.parse_args()

    result = verify_review_log(
        review_log_path=Path(args.review_log),
        hash_path=Path(args.hash_file),
        sig_path=Path(args.sig_file),
        public_key_path=Path(args.public_key),
    )

    print("[OK] signature_verified:", result["signature_verified"])
    print("[OK] review_count:", result["review_count"])
    print("[OK] merkle_root:", result["merkle_root"])
    print("[OK] review_log_hash:", result["review_log_hash"])


if __name__ == "__main__":
    main()
