#!/usr/bin/env python3
import argparse
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True)
    parser.add_argument("--private-key", default="keys/ed25519_private.pem")
    args = parser.parse_args()

    review_path = Path(args.review)
    key_path = Path(args.private_key)

    review_bytes = review_path.read_bytes()
    private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    signature = private_key.sign(review_bytes)

    sig_path = review_path.with_suffix(review_path.suffix + ".sig")
    sig_path.write_text(base64.b64encode(signature).decode("ascii") + "\n", encoding="utf-8")

    print(f"[OK] signed: {review_path}")
    print(f"[OK] signature: {sig_path}")

if __name__ == "__main__":
    main()
