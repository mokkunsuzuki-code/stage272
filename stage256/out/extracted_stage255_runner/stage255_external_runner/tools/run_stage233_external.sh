#!/bin/bash
set -e

echo "=== Stage233: External Signature Verification ==="

python3 tools/verify_external_signatures.py

echo "[DONE] External verification complete"
