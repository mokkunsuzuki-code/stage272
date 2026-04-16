#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


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
    parser = argparse.ArgumentParser(description="Sign fail evidence with Ed25519")
    parser.add_argument("--evidence", required=True, help="Path to fail evidence JSON")
    parser.add_argument("--private-key", required=True, help="Path to Ed25519 private key PEM")
    parser.add_argument("--public-key", required=True, help="Path to Ed25519 public key PEM")
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    private_key_path = Path(args.private_key)
    public_key_path = Path(args.public_key)

    if not evidence_path.exists():
        raise SystemExit(f"[ERROR] evidence file not found: {evidence_path}")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    if evidence.get("type") != "fail_evidence":
        raise SystemExit(f"[ERROR] unsupported evidence type: {evidence.get('type')}")

    payload_bytes = canonical_json_bytes(build_signing_payload(evidence))

    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=None,
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("Provided private key is not an Ed25519 private key")

    signature = private_key.sign(payload_bytes)
    signature_b64 = base64.b64encode(signature).decode("ascii")
    public_key_pem = public_key_path.read_text(encoding="utf-8")

    evidence["signature"] = signature_b64
    evidence["public_key"] = public_key_pem
    evidence["status"] = "signed"

    evidence_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("[OK] signed evidence:", evidence_path)
    print("[OK] status: signed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
