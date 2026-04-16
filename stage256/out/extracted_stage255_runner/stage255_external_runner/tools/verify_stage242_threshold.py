#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_signer_map(config: dict) -> dict:
    return {signer["id"]: signer for signer in config["signers"]}


def verify_one_signature(sig_path: Path, signer_map: dict, artifact_path: Path, artifact_hash: str) -> dict | None:
    data = load_json(sig_path)
    signer_id = data.get("signer_id")

    if signer_id not in signer_map:
        print(f"[FAIL] unknown signer in {sig_path.name}: {signer_id}")
        return None

    signer = signer_map[signer_id]

    if data.get("artifact_path") != str(artifact_path):
        print(f"[FAIL] artifact path mismatch in {sig_path.name}")
        return None

    if data.get("artifact_sha256") != artifact_hash:
        print(f"[FAIL] artifact hash mismatch in {sig_path.name}")
        return None

    pub_path = Path(signer["public_key"])
    if not pub_path.exists():
        print(f"[FAIL] public key missing for signer {signer_id}: {pub_path}")
        return None

    public_key = serialization.load_pem_public_key(pub_path.read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        print(f"[FAIL] public key is not Ed25519 for signer {signer_id}")
        return None

    try:
        signature = base64.b64decode(data["signature_b64"])
        public_key.verify(signature, bytes.fromhex(artifact_hash))
    except (InvalidSignature, ValueError, KeyError) as exc:
        print(f"[FAIL] invalid signature for {signer_id}: {exc}")
        return None

    result = {
        "signer_id": signer["id"],
        "role": signer["role"],
        "independence_group": signer["independence_group"],
        "signature_file": str(sig_path),
    }
    print(f"[OK] valid signature: {signer['id']} ({signer['role']})")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--signatures-dir", default="signatures")
    args = parser.parse_args()

    config = load_yaml(Path(args.config))
    signer_map = build_signer_map(config)

    policy = config["policy"]
    threshold = int(policy["threshold"])
    require_external = bool(policy.get("require_external", False))
    min_groups = int(policy.get("min_independence_groups", 1))

    artifact_path = Path(policy["artifact_path"])
    if not artifact_path.exists():
        raise SystemExit(f"Artifact not found: {artifact_path}")

    artifact_hash = sha256_file(artifact_path)
    print(f"[INFO] artifact: {artifact_path}")
    print(f"[INFO] sha256:   {artifact_hash}")

    sig_dir = Path(args.signatures_dir)
    if not sig_dir.exists():
        raise SystemExit(f"Signatures directory not found: {sig_dir}")

    valid = []
    seen_signers = set()

    for sig_path in sorted(sig_dir.glob("*.sig.json")):
        result = verify_one_signature(sig_path, signer_map, artifact_path, artifact_hash)
        if result is None:
            continue

        signer_id = result["signer_id"]
        if signer_id in seen_signers:
            print(f"[FAIL] duplicate signer detected: {signer_id}")
            continue

        seen_signers.add(signer_id)
        valid.append(result)

    valid_count = len(valid)
    independence_groups = {item["independence_group"] for item in valid}
    external_present = any(item["independence_group"] == "external" for item in valid)

    print(f"[INFO] valid signatures: {valid_count}")
    print(f"[INFO] independence groups: {sorted(independence_groups)}")
    print(f"[INFO] external present: {external_present}")

    if valid_count < threshold:
        raise SystemExit(f"[FAIL] threshold not met: need {threshold}, got {valid_count}")

    if len(independence_groups) < min_groups:
        raise SystemExit(
            f"[FAIL] independence group policy not met: need {min_groups}, got {len(independence_groups)}"
        )

    if require_external and not external_present:
        raise SystemExit("[FAIL] external signer required but not present")

    print("[OK] stage242 policy satisfied")
    print("[OK] threshold approval passed")


if __name__ == "__main__":
    main()
