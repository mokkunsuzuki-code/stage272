#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p out/bundle

python3 tools/build_signed_evidence_bundle.py \
  --repo-root . \
  --output-dir out/bundle \
  --private-key keys/checkpoint_signing_private.pem

python3 tools/verify_signed_evidence_bundle.py \
  --repo-root . \
  --bundle-dir out/bundle \
  --public-key keys/checkpoint_signing_public.pem

echo "[OK] Stage230 signed evidence bundle complete"
