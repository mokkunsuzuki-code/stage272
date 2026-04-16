#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_signer(config: dict, signer_id: str) -> dict:
    for signer in config["signers"]:
        if signer["id"] == signer_id:
            return signer
    raise SystemExit(f"Signer not found in config: {signer_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--signer-id", required=True)
    parser.add_argument("--output-dir", default="signatures")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    signer = find_signer(config, args.signer_id)

    artifact_path = Path(config["policy"]["artifact_path"])
    if not artifact_path.exists():
        raise SystemExit(f"Artifact not found: {artifact_path}")

    private_key_path = Path(signer["private_key"])
    if not private_key_path.exists():
        raise SystemExit(f"Private key not found: {private_key_path}")

    artifact_hash = sha256_file(artifact_path)

    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=None,
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise SystemExit("Loaded private key is not an Ed25519 private key.")

    signature = private_key.sign(bytes.fromhex(artifact_hash))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.signer_id}.sig.json"

    payload = {
        "stage": "stage242",
        "signer_id": signer["id"],
        "role": signer["role"],
        "independence_group": signer["independence_group"],
        "artifact_path": str(artifact_path),
        "artifact_sha256": artifact_hash,
        "public_key": signer["public_key"],
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }

    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] wrote signature: {out_path}")


if __name__ == "__main__":
    main()
