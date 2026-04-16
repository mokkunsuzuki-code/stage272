#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "[1] ensure dependency"
python3 - << 'PY'
import importlib.util
import sys
if importlib.util.find_spec("yaml") is None:
    sys.exit(1)
PY
if [ $? -ne 0 ]; then
  python3 -m pip install pyyaml
fi

echo "[2] build claim bundle"
python3 tools/build_claim_bundle.py --claims claims/claims.yaml --out-dir out/proofs

echo "[3] verify security claims"
python3 tools/verify_claims.py --claims claims/claims.yaml --bundle-dir out/proofs

echo "[OK] Stage222 verification completed"
