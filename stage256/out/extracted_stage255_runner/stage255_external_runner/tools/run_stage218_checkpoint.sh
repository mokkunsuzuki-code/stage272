#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/transparency
mkdir -p out/transparency/inclusion_proofs
mkdir -p out/checkpoint

python3 tools/build_transparency_log.py --input-dir out --output-dir out/transparency

python3 tools/sign_checkpoint.py \
  --merkle-tree out/transparency/merkle_tree.json \
  --transparency-log out/transparency/transparency_log.json \
  --private-key keys/checkpoint_private.pem \
  --public-key keys/checkpoint_public.pem \
  --output-dir out/checkpoint \
  --log-id "qsp-stage218-log" \
  --origin "QSP Transparency Log"

python3 tools/verify_checkpoint.py \
  --checkpoint out/checkpoint/checkpoint.json

echo "[OK] Stage218 checkpoint flow completed"
