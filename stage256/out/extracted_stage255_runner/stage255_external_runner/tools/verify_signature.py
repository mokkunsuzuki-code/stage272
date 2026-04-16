#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_json_bytes(data: dict) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def build_signing_payload(evidence: dict) -> dict:
    return {
        "version": evidence.get("version"),
        "type": evidence.get("type"),
        "log_file": evidence.get("log_file"),
        "sha256": evidence.get("sha256"),
        "size_bytes": evidence.get("size_bytes"),
        "line_count": evidence.get("line_count"),
        "status": "unsigned",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify signed fail evidence")
    parser.add_argument("--evidence", required=True, help="Path to signed fail evidence JSON")
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    if not evidence_path.exists():
        raise SystemExit(f"[ERROR] evidence file not found: {evidence_path}")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    required = [
        "version",
        "type",
        "log_file",
        "sha256",
        "size_bytes",
        "line_count",
        "status",
        "signature",
        "public_key",
    ]
    for key in required:
        if key not in evidence:
            raise ValueError(f"Missing required field: {key}")

    if evidence["type"] != "fail_evidence":
        raise SystemExit(f"[ERROR] unsupported evidence type: {evidence['type']}")

    payload_bytes = canonical_json_bytes(build_signing_payload(evidence))

    public_key = serialization.load_pem_public_key(
        evidence["public_key"].encode("utf-8")
    )
    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError("Provided public key is not an Ed25519 public key")

    signature = base64.b64decode(evidence["signature"])
    public_key.verify(signature, payload_bytes)

    print("[OK] signature verification passed:", evidence_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
