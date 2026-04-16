#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/session out/anchors out/witnesses out/checkpoints

python3 tools/run_real_qsp_session.py
python3 tools/build_session_manifest.py \
  --session-result out/session/qsp_session_result.json \
  --output out/session/session_manifest.json

python3 tools/sign_session_manifest.py \
  --manifest out/session/session_manifest.json

cp out/session/session_manifest.json out/anchors/session_manifest.json
cp out/session/session_manifest.json.sha256 out/anchors/session_manifest.json.sha256

echo "[OK] Stage254 real QSP session anchoring completed"
