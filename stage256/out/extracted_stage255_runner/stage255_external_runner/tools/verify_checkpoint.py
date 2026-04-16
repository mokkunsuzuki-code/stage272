#!/usr/bin/env python3

import argparse
import base64
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Verify signed transparency checkpoint")
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint.json")
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))

    required = [
        "version",
        "type",
        "log_id",
        "origin",
        "tree_size",
        "root_hash",
        "generated_at",
        "hash_algorithm",
        "signature_algorithm",
        "signature",
        "public_key_pem",
    ]
    for key in required:
        if key not in checkpoint:
            raise SystemExit(f"ERROR: missing field in checkpoint.json: {key}")

    unsigned = {
        "version": checkpoint["version"],
        "type": checkpoint["type"],
        "log_id": checkpoint["log_id"],
        "origin": checkpoint["origin"],
        "tree_size": checkpoint["tree_size"],
        "root_hash": checkpoint["root_hash"],
        "generated_at": checkpoint["generated_at"],
        "hash_algorithm": checkpoint["hash_algorithm"],
        "signature_algorithm": checkpoint["signature_algorithm"],
    }

    canonical = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    sig_bytes = base64.b64decode(checkpoint["signature"])
    pubkey_pem = checkpoint["public_key_pem"].encode("utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        payload_path = tmpdir / "payload.bin"
        sig_path = tmpdir / "sig.bin"
        pub_path = tmpdir / "pub.pem"

        payload_path.write_bytes(canonical)
        sig_path.write_bytes(sig_bytes)
        pub_path.write_bytes(pubkey_pem)

        proc = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(pub_path),
                "-sigfile",
                str(sig_path),
                "-rawin",
                "-in",
                str(payload_path),
            ],
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            raise SystemExit("ERROR: checkpoint verification failed")

    print("[OK] checkpoint signature verified")
    print(f"[OK] log_id: {checkpoint['log_id']}")
    print(f"[OK] tree_size: {checkpoint['tree_size']}")
    print(f"[OK] root_hash: {checkpoint['root_hash']}")


if __name__ == "__main__":
    main()
