#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Stage227 attack simulation start"

mkdir -p out/attacks

python3 tools/run_attack_simulation.py

echo "[INFO] Stage227 attack simulation done"
