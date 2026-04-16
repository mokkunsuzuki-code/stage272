#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_keypair(private_key_path: Path, public_key_path: Path) -> None:
    if private_key_path.exists() and public_key_path.exists():
        return

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def load_private_key(path: Path) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def sign_json(payload: dict, private_key: Ed25519PrivateKey) -> dict:
    payload_bytes = canonical_json_bytes(payload)
    signature = private_key.sign(payload_bytes)
    return {
        "payload": payload,
        "signature_b64": base64.b64encode(signature).decode("ascii"),
    }


def build_local_witness(manifest: dict, manifest_path: Path) -> dict:
    return {
        "schema": "qsp_local_witness/v1",
        "created_at": utc_now(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest["manifest_sha256"],
        "transcript_hash": manifest["binding"]["transcript_hash"],
        "session_id": manifest["session"]["session_id"],
        "witness_type": "local_witness",
    }


def build_checkpoint_witness(manifest: dict, manifest_path: Path, previous_checkpoint_sha256: str | None) -> dict:
    checkpoint_core = {
        "schema": "qsp_checkpoint_witness/v1",
        "created_at": utc_now(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest["manifest_sha256"],
        "session_id": manifest["session"]["session_id"],
        "epoch": manifest["session"]["epoch"],
        "transcript_hash": manifest["binding"]["transcript_hash"],
        "previous_checkpoint_sha256": previous_checkpoint_sha256,
        "witness_type": "checkpoint_witness",
    }
    checkpoint_core["checkpoint_sha256"] = sha256_hex(canonical_json_bytes(checkpoint_core))
    return checkpoint_core


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="out/session/session_manifest.json")
    parser.add_argument("--local-private", default="keys/local_witness_private.pem")
    parser.add_argument("--local-public", default="keys/local_witness_public.pem")
    parser.add_argument("--checkpoint-private", default="keys/checkpoint_witness_private.pem")
    parser.add_argument("--checkpoint-public", default="keys/checkpoint_witness_public.pem")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    local_private_path = Path(args.local_private)
    local_public_path = Path(args.local_public)
    checkpoint_private_path = Path(args.checkpoint_private)
    checkpoint_public_path = Path(args.checkpoint_public)

    ensure_keypair(local_private_path, local_public_path)
    ensure_keypair(checkpoint_private_path, checkpoint_public_path)

    local_private = load_private_key(local_private_path)
    checkpoint_private = load_private_key(checkpoint_private_path)

    witnesses_dir = Path("out/witnesses")
    checkpoints_dir = Path("out/checkpoints")
    history_dir = checkpoints_dir / "history"
    witnesses_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    local_witness_core = build_local_witness(manifest, manifest_path)
    local_witness_signed = sign_json(local_witness_core, local_private)
    local_witness_path = witnesses_dir / "local_witness.json"
    local_witness_path.write_text(json.dumps(local_witness_signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    existing = sorted(history_dir.glob("checkpoint_*.json"))
    previous_checkpoint_sha256 = None
    next_index = len(existing) + 1
    if existing:
        previous = json.loads(existing[-1].read_text(encoding="utf-8"))
        previous_checkpoint_sha256 = previous["payload"]["checkpoint_sha256"]

    checkpoint_core = build_checkpoint_witness(manifest, manifest_path, previous_checkpoint_sha256)
    checkpoint_signed = sign_json(checkpoint_core, checkpoint_private)

    latest_checkpoint_path = checkpoints_dir / "checkpoint_witness.json"
    history_checkpoint_path = history_dir / f"checkpoint_{next_index:04d}.json"

    latest_checkpoint_path.write_text(json.dumps(checkpoint_signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    history_checkpoint_path.write_text(json.dumps(checkpoint_signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index = {
        "schema": "qsp_checkpoint_index/v1",
        "updated_at": utc_now(),
        "count": next_index,
        "entries": [
            {
                "index": i + 1,
                "path": f"out/checkpoints/history/{path.name}",
            }
            for i, path in enumerate(sorted(history_dir.glob("checkpoint_*.json")))
        ],
    }
    (checkpoints_dir / "checkpoint_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[OK] wrote: {local_witness_path}")
    print(f"[OK] wrote: {latest_checkpoint_path}")
    print(f"[OK] wrote: {history_checkpoint_path}")
    print(f"[OK] wrote: {checkpoints_dir / 'checkpoint_index.json'}")


if __name__ == "__main__":
    main()
