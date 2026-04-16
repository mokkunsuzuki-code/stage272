#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ARTIFACT="stage241-source-bundle.tar.gz"
mkdir -p signatures out/multi_party

if [ ! -f "$ARTIFACT" ]; then
  echo "[ERROR] $ARTIFACT が見つかりません"
  exit 1
fi

openssl pkeyutl -sign \
  -inkey keys/owner_private.pem \
  -rawin \
  -in "$ARTIFACT" \
  -out signatures/owner.sig

openssl pkeyutl -sign \
  -inkey keys/auditor_private.pem \
  -rawin \
  -in "$ARTIFACT" \
  -out signatures/auditor.sig

echo "[OK] signed: signatures/owner.sig"
echo "[OK] signed: signatures/auditor.sig"
