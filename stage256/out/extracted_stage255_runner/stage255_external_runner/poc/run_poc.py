#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path


OUT_DIR = Path("out/poc")
RESULT_FILE = OUT_DIR / "result.json"


def generate_key() -> bytes:
    return os.urandom(32)


def derive_shared_key(alice_key: bytes, bob_key: bytes) -> str:
    material = alice_key + bob_key
    return hashlib.sha256(material).hexdigest()


def simulate() -> dict:
    print("[*] Generating keys...")
    alice_key = generate_key()
    bob_key = generate_key()

    print("[*] Deriving shared key...")
    shared_key = derive_shared_key(alice_key, bob_key)

    result = {
        "stage": "Stage226",
        "poc": "minimal-executable-poc",
        "status": "success",
        "alice_key_length": len(alice_key),
        "bob_key_length": len(bob_key),
        "shared_key_sha256_hex_length": len(shared_key),
        "shared_key": shared_key,
    }

    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    result = simulate()

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("[OK] Shared key:", result["shared_key"])
    print("[OK] Wrote evidence:", RESULT_FILE)


if __name__ == "__main__":
    main()
