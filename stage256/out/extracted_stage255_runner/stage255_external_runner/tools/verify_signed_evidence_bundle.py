#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_public_key(public_key_path: Path) -> Ed25519PublicKey:
    pem = public_key_path.read_bytes()
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("public key is not an Ed25519 public key")
    return key


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify signed evidence bundle")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--bundle-dir", default="out/bundle", help="bundle directory")
    parser.add_argument(
        "--public-key",
        default="keys/checkpoint_signing_public.pem",
        help="Ed25519 public key PEM",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    bundle_dir = (repo_root / args.bundle_dir).resolve()

    payload_path = bundle_dir / "evidence_bundle_payload.json"
    signature_path = bundle_dir / "evidence_bundle_signature.json"
    public_key_path = (repo_root / args.public_key).resolve()

    if not payload_path.exists():
        raise FileNotFoundError(f"missing payload: {payload_path}")
    if not signature_path.exists():
        raise FileNotFoundError(f"missing signature: {signature_path}")
    if not public_key_path.exists():
        raise FileNotFoundError(f"missing public key: {public_key_path}")

    payload: Dict[str, Any] = json.loads(payload_path.read_text(encoding="utf-8"))
    signature_doc: Dict[str, Any] = json.loads(signature_path.read_text(encoding="utf-8"))

    payload_bytes = canonical_json_bytes(payload)
    computed_payload_sha256 = sha256_bytes(payload_bytes)
    expected_payload_sha256 = signature_doc["payload_sha256"]

    if computed_payload_sha256 != expected_payload_sha256:
        raise ValueError(
            f"payload sha256 mismatch: expected={expected_payload_sha256} got={computed_payload_sha256}"
        )

    public_key = load_public_key(public_key_path)
    signature = base64.b64decode(signature_doc["signature_base64"])
    public_key.verify(signature, payload_bytes)

    verified_files = 0
    for entry in payload["files"]:
        rel = entry["path"]
        expected = entry["sha256"]
        file_path = (repo_root / rel).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"missing bundled file: {rel}")
        actual = sha256_file(file_path)
        if actual != expected:
            raise ValueError(f"file hash mismatch: {rel}: expected={expected} got={actual}")
        verified_files += 1

    print(f"[OK] signature verified")
    print(f"[OK] payload_sha256: {computed_payload_sha256}")
    print(f"[OK] verified_files: {verified_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
