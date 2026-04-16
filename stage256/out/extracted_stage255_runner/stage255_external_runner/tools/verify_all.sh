#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1] rebuild transparency log"
python3 tools/build_transparency_log.py --input-dir out --output-dir out/transparency

echo "[2] archive current checkpoint into history"
python3 tools/archive_checkpoint.py

echo "[3] verify transparency log + Merkle tree + checkpoint history"
python3 tools/verify_transparency_log.py

echo "[4] run external monitor"
python3 tools/external_monitor.py

echo "[OK] independent verification completed"
