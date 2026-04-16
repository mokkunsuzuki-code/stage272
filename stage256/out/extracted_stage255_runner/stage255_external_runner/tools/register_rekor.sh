#!/usr/bin/env bash
set -e

FILE="$1"

rekor-cli upload \
  --artifact "$FILE" \
  --rekor_server https://rekor.sigstore.dev

echo "[OK] uploaded to Rekor"
