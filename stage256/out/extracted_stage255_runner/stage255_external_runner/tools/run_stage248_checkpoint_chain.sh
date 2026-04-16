#!/usr/bin/env bash
set -euo pipefail

mkdir -p keys out/review_log out/review_log_history

# CI/ローカル両対応: 毎回同一実行中に署名→検証
openssl genpkey -algorithm Ed25519 -out keys/owner_private.pem
openssl pkey -in keys/owner_private.pem -pubout -out keys/owner_public.pem

python3 tools/build_review_log.py \
  --source-dir review_records \
  --output-dir out/review_log \
  --private-key keys/owner_private.pem

python3 tools/verify_review_log.py \
  --review-log out/review_log/review_log.json \
  --hash-file out/review_log/review_log_hash.txt \
  --sig-file out/review_log/review_log.sig \
  --public-key keys/owner_public.pem

python3 tools/create_review_checkpoint.py \
  --review-log out/review_log/review_log.json \
  --review-log-hash out/review_log/review_log_hash.txt \
  --history-dir out/review_log_history \
  --private-key keys/owner_private.pem

python3 tools/verify_checkpoint_chain.py \
  --history-dir out/review_log_history \
  --public-key keys/owner_public.pem

echo "[OK] Stage248 checkpoint chain completed."
