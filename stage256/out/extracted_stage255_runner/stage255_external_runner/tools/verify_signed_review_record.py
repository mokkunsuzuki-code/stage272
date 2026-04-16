#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization

def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(description="Verify signed Stage245 review record")
    parser.add_argument("--input", required=True, help="Path to review record JSON")
    parser.add_argument("--signature", required=True, help="Path to signature JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    sig_path = Path(args.signature)

    if not input_path.exists():
        fail(f"input file not found: {input_path}")
    if not sig_path.exists():
        fail(f"signature file not found: {sig_path}")

    payload = input_path.read_bytes()
    try:
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid signature JSON: {exc}")

    required = {"version", "input_file", "public_key", "signature_base64"}
    missing = required - set(sig_data.keys())
    if missing:
        fail(f"missing signature fields: {sorted(missing)}")

    pub_path = Path(sig_data["public_key"])
    if not pub_path.exists():
        fail(f"public key not found: {pub_path}")

    public_key = serialization.load_pem_public_key(pub_path.read_bytes())
    signature = base64.b64decode(sig_data["signature_base64"])

    try:
        public_key.verify(signature, payload)
    except Exception as exc:
        fail(f"signature verification failed: {exc}")

    print("[OK] signed review record is valid")

if __name__ == "__main__":
    main()
