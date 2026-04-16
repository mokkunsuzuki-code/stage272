#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


KEY_SPECS = [
    ("developer_private.pem", "developer_public.pem"),
    ("auditor_private.pem", "auditor_public.pem"),
    ("reviewer_private.pem", "reviewer_public.pem"),
]


def write_keypair(keys_dir: Path, private_name: str, public_name: str) -> None:
    private_path = keys_dir / private_name
    public_path = keys_dir / public_name

    if private_path.exists() and public_path.exists():
        print(f"[SKIP] keys already exist: {private_name}, {public_name}")
        return

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

    private_path.chmod(0o600)
    public_path.chmod(0o644)

    print(f"[OK] wrote private key: {private_path}")
    print(f"[OK] wrote public key:  {public_path}")


def main() -> None:
    keys_dir = Path("keys")
    keys_dir.mkdir(parents=True, exist_ok=True)

    for private_name, public_name in KEY_SPECS:
        write_keypair(keys_dir, private_name, public_name)


if __name__ == "__main__":
    main()
