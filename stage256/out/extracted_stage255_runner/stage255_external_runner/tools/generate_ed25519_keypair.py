#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Ed25519 keypair")
    parser.add_argument("--private", required=True, help="Private key PEM output path")
    parser.add_argument("--public", required=True, help="Public key PEM output path")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    private_path = Path(args.private)
    public_path = Path(args.public)

    if not args.force:
        for path in (private_path, public_path):
            if path.exists():
                raise SystemExit(f"[ERROR] already exists: {path}")

    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path.write_bytes(private_bytes)
    public_path.write_bytes(public_bytes)

    print(f"[OK] wrote private key: {private_path}")
    print(f"[OK] wrote public key:  {public_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
