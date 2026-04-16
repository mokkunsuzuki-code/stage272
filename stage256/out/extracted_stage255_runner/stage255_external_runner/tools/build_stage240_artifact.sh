#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/external_verification
ARTIFACT="stage240-source-bundle.tar.gz"

rm -f "$ARTIFACT"

if [ -f README.md ]; then
  tar -czf "$ARTIFACT" \
    README.md \
    LICENSE \
    tools \
    docs \
    .github \
    policy
else
  echo "[ERROR] README.md が見つかりません"
  exit 1
fi

shasum -a 256 "$ARTIFACT" | tee out/external_verification/stage240-source-bundle.sha256
echo "[OK] built: $ARTIFACT"
