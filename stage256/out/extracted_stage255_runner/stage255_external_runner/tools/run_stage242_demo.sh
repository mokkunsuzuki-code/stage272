#!/usr/bin/env bash
set -euo pipefail

echo "[STEP] clean"
rm -rf signatures out/stage242
mkdir -p signatures out/stage242

echo "[STEP] generate keys"
python3 tools/generate_stage242_keys.py

echo "[STEP] build manifest"
python3 tools/build_stage242_manifest.py

echo "[STEP] sign by developer"
python3 tools/sign_stage242_artifact.py \
  --config docs/stage242_policy.yaml \
  --signer-id developer

echo "[STEP] sign by auditor"
python3 tools/sign_stage242_artifact.py \
  --config docs/stage242_policy.yaml \
  --signer-id auditor

echo "[STEP] verify (expected to FAIL because external reviewer is missing)"
if python3 tools/verify_stage242_threshold.py \
  --config docs/stage242_policy.yaml \
  --signatures-dir signatures; then
  echo "[UNEXPECTED] verification passed without external reviewer"
  exit 1
else
  echo "[OK] failed as expected without external reviewer"
fi

echo "[STEP] sign by reviewer"
python3 tools/sign_stage242_artifact.py \
  --config docs/stage242_policy.yaml \
  --signer-id reviewer

echo "[STEP] verify again (expected to PASS)"
python3 tools/verify_stage242_threshold.py \
  --config docs/stage242_policy.yaml \
  --signatures-dir signatures

echo "[DONE] stage242 demo completed"
