#!/usr/bin/env bash
set -e

UUID="$1"

rekor-cli get \
  --uuid "$UUID" \
  --rekor_server https://rekor.sigstore.dev

echo "[OK] Rekor verified"
