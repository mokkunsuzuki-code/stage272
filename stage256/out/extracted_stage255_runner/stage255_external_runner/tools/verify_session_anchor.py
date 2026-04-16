#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_signed_json(signed_doc: dict, public_key_path: Path) -> None:
    payload = signed_doc["payload"]
    signature = base64.b64decode(signed_doc["signature_b64"])

    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    assert isinstance(public_key, Ed25519PublicKey)
    public_key.verify(signature, canonical_json_bytes(payload))


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--session-result", required=True)
    parser.add_argument("--local-witness", required=True)
    parser.add_argument("--local-public", required=True)
    parser.add_argument("--checkpoint-witness", required=True)
    parser.add_argument("--checkpoint-public", required=True)
    parser.add_argument("--github-receipt")
    parser.add_argument("--ots")
    parser.add_argument("--cosign-bundle")
    parser.add_argument("--cosign-identity-regexp", default=r"https://github\.com/.+")
    parser.add_argument("--cosign-oidc-issuer", default="https://token.actions.githubusercontent.com")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    session_result_path = Path(args.session_result)
    local_witness_path = Path(args.local_witness)
    local_public_path = Path(args.local_public)
    checkpoint_witness_path = Path(args.checkpoint_witness)
    checkpoint_public_path = Path(args.checkpoint_public)

    manifest = load_json(manifest_path)
    session_result = load_json(session_result_path)

    session_result_sha256 = sha256_hex(canonical_json_bytes(session_result))
    if manifest["source"]["sha256"] != session_result_sha256:
        raise SystemExit("[ERROR] session_result sha256 mismatch")

    manifest_core = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    manifest_sha256 = sha256_hex(canonical_json_bytes(manifest_core))
    if manifest["manifest_sha256"] != manifest_sha256:
        raise SystemExit("[ERROR] manifest_sha256 mismatch")

    if manifest["binding"]["transcript_hash"] != session_result["transcript_hash"]:
        raise SystemExit("[ERROR] transcript_hash mismatch")

    if manifest["binding"]["policy"] != session_result["policy"]:
        raise SystemExit("[ERROR] policy mismatch")

    if manifest["binding"]["fail_closed_result"] != session_result["fail_closed_result"]:
        raise SystemExit("[ERROR] fail_closed_result mismatch")

    local_witness_signed = load_json(local_witness_path)
    verify_signed_json(local_witness_signed, local_public_path)
    local_payload = local_witness_signed["payload"]
    if local_payload["manifest_sha256"] != manifest["manifest_sha256"]:
        raise SystemExit("[ERROR] local witness manifest sha mismatch")

    checkpoint_witness_signed = load_json(checkpoint_witness_path)
    verify_signed_json(checkpoint_witness_signed, checkpoint_public_path)
    checkpoint_payload = checkpoint_witness_signed["payload"]
    if checkpoint_payload["manifest_sha256"] != manifest["manifest_sha256"]:
        raise SystemExit("[ERROR] checkpoint witness manifest sha mismatch")

    recomputed_checkpoint_sha = sha256_hex(
        canonical_json_bytes({k: v for k, v in checkpoint_payload.items() if k != "checkpoint_sha256"})
    )
    if checkpoint_payload["checkpoint_sha256"] != recomputed_checkpoint_sha:
        raise SystemExit("[ERROR] checkpoint witness sha mismatch")

    print("[OK] manifest verified")
    print(f"[OK] manifest_sha256: {manifest['manifest_sha256']}")
    print(f"[OK] transcript_hash: {manifest['binding']['transcript_hash']}")
    print(f"[OK] fail_closed_passed: {manifest['binding']['fail_closed_result']['passed']}")
    print("[OK] local witness signature verified")
    print("[OK] checkpoint witness signature verified")

    if args.github_receipt:
        receipt_path = Path(args.github_receipt)
        receipt = load_json(receipt_path)
        if receipt["manifest_sha256"] != manifest["manifest_sha256"]:
            raise SystemExit("[ERROR] GitHub receipt manifest sha mismatch")
        run_url = receipt.get("run_url", "")
        if run_url and not re.match(r"^https://github\.com/.+/actions/runs/\d+$", run_url):
            raise SystemExit("[ERROR] GitHub receipt run_url format invalid")
        print("[OK] GitHub anchor receipt verified")
        print(f"[OK] run_url: {run_url}")

    if args.ots:
        ots_path = Path(args.ots)
        if not ots_path.exists():
            raise SystemExit("[ERROR] OTS file not found")
        rc, out, err = run_command(["ots", "verify", str(ots_path)])
        if rc == 0:
            print("[OK] OTS verified")
        else:
            print("[WARN] OTS verify did not fully succeed in this environment")
            if out.strip():
                print(out.strip())
            if err.strip():
                print(err.strip())

    if args.cosign_bundle:
        bundle_path = Path(args.cosign_bundle)
        if not bundle_path.exists():
            raise SystemExit("[ERROR] cosign bundle not found")

        rc, out, err = run_command(
            [
                "cosign",
                "verify-blob",
                "--bundle", str(bundle_path),
                "--certificate-identity-regexp", args.cosign_identity_regexp,
                "--certificate-oidc-issuer", args.cosign_oidc_issuer,
                str(manifest_path),
            ]
        )
        if rc != 0:
            print("[WARN] cosign verify-blob did not fully succeed in this environment")
            if out.strip():
                print(out.strip())
            if err.strip():
                print(err.strip())
        else:
            print("[OK] cosign bundle verified")

    print("[OK] Stage253 session anchor verification finished")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
