#!/usr/bin/env python3
import argparse
import base64
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def load_or_create_private_key(path: Path) -> Ed25519PrivateKey:
    if path.exists():
        key_data = path.read_bytes()
        return serialization.load_pem_private_key(key_data, password=None)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pem)
    return key

def write_public_key(private_key: Ed25519PrivateKey, path: Path) -> None:
    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pem)

def main() -> None:
    parser = argparse.ArgumentParser(description="Sign Stage245 review record")
    parser.add_argument("--input", required=True, help="Path to review record JSON")
    parser.add_argument("--signature-output", required=True, help="Path to output signature JSON")
    parser.add_argument("--private-key", default="keys/review_record_private.pem", help="Private key path")
    parser.add_argument("--public-key", default="keys/review_record_public.pem", help="Public key path")
    args = parser.parse_args()

    input_path = Path(args.input)
    sig_path = Path(args.signature_output)
    priv_path = Path(args.private_key)
    pub_path = Path(args.public_key)

    payload = input_path.read_bytes()
    private_key = load_or_create_private_key(priv_path)
    write_public_key(private_key, pub_path)

    signature = private_key.sign(payload)
    bundle = {
        "version": 1,
        "input_file": str(input_path),
        "public_key": str(pub_path),
        "signature_base64": base64.b64encode(signature).decode("ascii")
    }

    sig_path.parent.mkdir(parents=True, exist_ok=True)
    sig_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] signed: {input_path}")
    print(f"[OK] wrote: {sig_path}")
    print(f"[OK] wrote: {pub_path}")

if __name__ == "__main__":
    main()
