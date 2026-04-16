#!/usr/bin/env bash
set -euo pipefail

python3 tools/generate_anchor_request.py

echo
echo "[INFO] anchor request generated"
echo "[INFO] files under out/anchors:"
find out/anchors -maxdepth 3 -type f | sort
