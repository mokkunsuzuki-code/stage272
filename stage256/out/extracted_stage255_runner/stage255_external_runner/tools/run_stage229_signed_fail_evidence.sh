#!/usr/bin/env bash
set -euo pipefail

FAIL_EVIDENCE_DIR="out/fail_evidence"
INDEX_PATH="$FAIL_EVIDENCE_DIR/index.json"

mkdir -p keys

if [ ! -f keys/fail_evidence_private.pem ] || [ ! -f keys/fail_evidence_public.pem ]; then
  python3 tools/generate_ed25519_keypair.py
fi

# Stage228の既存パイプラインを再利用
bash tools/run_stage228_fail_evidence.sh

if [ ! -f "$INDEX_PATH" ]; then
  echo "[ERROR] index not found: $INDEX_PATH"
  exit 1
fi

# SHA256整合性検証
python3 tools/verify_fail_evidence.py --index "$INDEX_PATH"

# 各evidenceに署名
for evidence_file in "$FAIL_EVIDENCE_DIR"/*.evidence.json; do
  python3 tools/sign_fail_evidence.py \
    --evidence "$evidence_file" \
    --private-key keys/fail_evidence_private.pem \
    --public-key keys/fail_evidence_public.pem
done

# 各署名を検証
for evidence_file in "$FAIL_EVIDENCE_DIR"/*.evidence.json; do
  python3 tools/verify_signature.py --evidence "$evidence_file"
done

# 署名後のevidenceを含めて transparency log を再構築
python3 tools/build_transparency_log.py --input-dir out --output-dir out/transparency

# transparency log を検証
python3 tools/verify_transparency_log.py \
  --log out/transparency/transparency_log.json \
  --tree out/transparency/merkle_tree.json \
  --root out/transparency/root.txt

echo "[OK] Stage229 signed fail evidence pipeline completed"
