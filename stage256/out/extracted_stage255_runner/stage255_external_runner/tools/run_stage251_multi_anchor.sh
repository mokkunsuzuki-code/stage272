#!/usr/bin/env bash
set -euo pipefail

SUBJECT="downloaded_stage250_release_anchor/release_manifest.json"
GITHUB_RECEIPT="downloaded_stage250_release_anchor/github_release_anchor_receipt.json"

REQUEST="out/multi_anchor/request.json"
LOCAL_RECEIPT="out/multi_anchor/receipts/local_witness_receipt.json"
CHECKPOINT_RECEIPT="out/multi_anchor/receipts/checkpoint_witness_receipt.json"
GITHUB_NORMALIZED="out/multi_anchor/receipts/github_release_anchor_normalized.json"

mkdir -p keys out/multi_anchor/checkpoints out/multi_anchor/receipts

if [[ ! -f "$SUBJECT" ]]; then
  echo "[ERROR] missing subject: $SUBJECT"
  exit 1
fi

if [[ ! -f "$GITHUB_RECEIPT" ]]; then
  echo "[ERROR] missing GitHub receipt: $GITHUB_RECEIPT"
  exit 1
fi

if [[ ! -f "keys/witness_private.pem" || ! -f "keys/witness_public.pem" ]]; then
  python3 tools/generate_ed25519_keypair.py \
    --private keys/witness_private.pem \
    --public keys/witness_public.pem
fi

if [[ ! -f "keys/checkpoint_private.pem" || ! -f "keys/checkpoint_public.pem" ]]; then
  python3 tools/generate_ed25519_keypair.py \
    --private keys/checkpoint_private.pem \
    --public keys/checkpoint_public.pem
fi

python3 tools/build_multi_anchor_request.py \
  --subject "$SUBJECT" \
  --output "$REQUEST"

python3 tools/generate_local_witness_receipt.py \
  --request "$REQUEST" \
  --private-key keys/witness_private.pem \
  --key-id witness-key-1 \
  --output "$LOCAL_RECEIPT"

python3 tools/build_checkpoint_anchor.py \
  --request "$REQUEST" \
  --private-key keys/checkpoint_private.pem \
  --key-id checkpoint-key-1 \
  --checkpoint-dir out/multi_anchor/checkpoints \
  --output "$CHECKPOINT_RECEIPT"

python3 tools/import_github_anchor_receipt.py \
  --request "$REQUEST" \
  --manifest "$SUBJECT" \
  --receipt "$GITHUB_RECEIPT" \
  --output "$GITHUB_NORMALIZED"

python3 tools/verify_multi_anchor.py \
  --request "$REQUEST" \
  --policy anchors/policy.json \
  --receipts "$LOCAL_RECEIPT" "$CHECKPOINT_RECEIPT" "$GITHUB_NORMALIZED"

echo
echo "[OK] Stage251 multi-anchor completed"
find out/multi_anchor -maxdepth 3 -type f | sort
