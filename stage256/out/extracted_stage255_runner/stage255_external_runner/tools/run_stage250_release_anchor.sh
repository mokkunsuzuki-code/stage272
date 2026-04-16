#!/usr/bin/env bash
set -euo pipefail

python3 tools/generate_release_manifest.py --release-tag stage250-v1

echo
echo "[INFO] release anchor manifest generated"
echo "[INFO] files under out/release_anchor:"
find out/release_anchor -maxdepth 3 -type f | sort
