#!/bin/bash
set -euo pipefail

echo "[*] Running minimal executable PoC..."
python3 poc/run_poc.py

echo "[*] Verifying generated evidence..."

test -f out/poc/result.json

python3 - << 'PY'
import json

with open("out/poc/result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

assert data["stage"] == "Stage226", "stage mismatch"
assert data["poc"] == "minimal-executable-poc", "poc mismatch"
assert data["status"] == "success", "status mismatch"
assert data["alice_key_length"] == 32, "alice key length mismatch"
assert data["bob_key_length"] == 32, "bob key length mismatch"
assert data["shared_key_sha256_hex_length"] == 64, "shared key hex length mismatch"
assert isinstance(data["shared_key"], str) and len(data["shared_key"]) == 64, "shared key format mismatch"

print("[OK] Evidence verification passed.")
PY

echo "[OK] PoC executed and verified successfully."
