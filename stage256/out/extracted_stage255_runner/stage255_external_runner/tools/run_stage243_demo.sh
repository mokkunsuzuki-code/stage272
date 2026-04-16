#!/usr/bin/env bash
set -euo pipefail

echo "[STEP] clean"
rm -rf out/stage243
mkdir -p out/stage243
mkdir -p metadata/reviewers
mkdir -p keys

echo "[STEP] reset empty reviewer registry"
cat > metadata/reviewers/reviewer_registry.yaml << 'REG'
version: 1

reviewers: []
REG

echo "[STEP] build manifest"
python3 tools/build_stage243_manifest.py

echo "[STEP] verify registry (expected FAIL)"
if python3 tools/verify_stage243_registry.py; then
  echo "[UNEXPECTED] registry passed without active reviewer"
  exit 1
else
  echo "[OK] failed as expected because no active reviewer exists"
fi

echo "[STEP] prepare example reviewer public key"
cat > keys/reviewer_example_public.pem << 'KEY'
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA1111111111111111111111111111111111111111111=
-----END PUBLIC KEY-----
KEY

echo "[STEP] register example reviewer"
python3 tools/register_reviewer.py \
  --reviewer-id reviewer_example \
  --display-name "Example Reviewer" \
  --contact "example@example.com" \
  --key-path keys/reviewer_example_public.pem \
  --key-fingerprint "SHA256:examplefingerprint" \
  --status active \
  --scope release_manifest approval_policy

echo "[STEP] verify registry again (expected PASS)"
python3 tools/verify_stage243_registry.py

echo "[DONE] stage243 onboarding demo completed"
