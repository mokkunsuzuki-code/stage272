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

REQUIRED_FIELDS = {
    "review_id",
    "reviewer_id",
    "reviewer_type",
    "timestamp",
    "subject",
    "decision",
    "summary",
    "evidence_refs",
}


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


def load_review_record(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"{path} is missing fields: {sorted(missing)}")

    if not isinstance(data["evidence_refs"], list):
        raise ValueError(f"{path} field 'evidence_refs' must be a list")

    normalized = {
        "review_id": str(data["review_id"]),
        "reviewer_id": str(data["reviewer_id"]),
        "reviewer_type": str(data["reviewer_type"]),
        "timestamp": str(data["timestamp"]),
        "subject": str(data["subject"]),
        "decision": str(data["decision"]),
        "summary": str(data["summary"]),
        "evidence_refs": [str(x) for x in data["evidence_refs"]],
    }
    return normalized


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


def load_private_key(path: Path) -> Ed25519PrivateKey:
    pem = path.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(f"{path} is not an Ed25519 private key")
    return key


def build_review_log(source_dir: Path, output_dir: Path, private_key_path: Path) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    private_key_path = private_key_path.resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"review source directory not found: {source_dir}")

    review_files = sorted(source_dir.glob("*.json"))
    if not review_files:
        raise FileNotFoundError(f"no review records found in: {source_dir}")

    entries: list[dict[str, Any]] = []
    leaf_hashes: list[str] = []
    leaf_index: list[dict[str, str]] = []

    for review_file in review_files:
        entry = load_review_record(review_file)
        leaf_hash = sha256_hex(canonical_json_bytes(entry))
        entries.append(entry)
        leaf_hashes.append(leaf_hash)
        leaf_index.append(
            {
                "review_id": entry["review_id"],
                "source_file": review_file.name,
                "leaf_hash": leaf_hash,
            }
        )

    merkle_root = merkle_root_from_leaves(leaf_hashes)

    log_payload = {
        "version": 1,
        "type": "review_transparency_log",
        "generated_at": utc_now_iso(),
        "review_count": len(entries),
        "merkle_root": merkle_root,
        "leaf_hashes": leaf_index,
        "entries": entries,
    }

    canonical_payload = canonical_json_bytes(log_payload)
    review_log_hash = sha256_hex(canonical_payload)

    private_key = load_private_key(private_key_path)
    signature = private_key.sign(review_log_hash.encode("utf-8"))
    signature_b64 = base64.b64encode(signature).decode("ascii")

    output_dir.mkdir(parents=True, exist_ok=True)

    review_log_path = output_dir / "review_log.json"
    review_log_hash_path = output_dir / "review_log_hash.txt"
    review_log_sig_path = output_dir / "review_log.sig"

    with review_log_path.open("w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    review_log_hash_path.write_text(review_log_hash + "\n", encoding="utf-8")
    review_log_sig_path.write_text(signature_b64 + "\n", encoding="utf-8")

    return {
        "review_log_path": str(review_log_path),
        "review_log_hash_path": str(review_log_hash_path),
        "review_log_sig_path": str(review_log_sig_path),
        "review_count": len(entries),
        "merkle_root": merkle_root,
        "review_log_hash": review_log_hash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build signed review transparency log")
    parser.add_argument("--source-dir", default="review_records", help="Directory containing review JSON records")
    parser.add_argument("--output-dir", default="out/review_log", help="Directory to write review log artifacts")
    parser.add_argument("--private-key", default="keys/owner_private.pem", help="Ed25519 private key PEM")
    args = parser.parse_args()

    result = build_review_log(
        source_dir=Path(args.source_dir),
        output_dir=Path(args.output_dir),
        private_key_path=Path(args.private_key),
    )

    print("[OK] wrote:", result["review_log_path"])
    print("[OK] wrote:", result["review_log_hash_path"])
    print("[OK] wrote:", result["review_log_sig_path"])
    print("[OK] review_count:", result["review_count"])
    print("[OK] merkle_root:", result["merkle_root"])
    print("[OK] review_log_hash:", result["review_log_hash"])


if __name__ == "__main__":
    main()
