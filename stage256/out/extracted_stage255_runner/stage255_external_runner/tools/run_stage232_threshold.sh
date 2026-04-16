#!/bin/bash
set -e

echo "=== Stage232: Threshold Signature Check ==="

python3 tools/verify_threshold.py

echo "[DONE] Threshold verification complete"
