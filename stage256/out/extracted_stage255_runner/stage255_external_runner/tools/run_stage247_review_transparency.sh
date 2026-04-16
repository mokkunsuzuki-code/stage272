#!/usr/bin/env bash
set -euo pipefail

mkdir -p keys out/review_log

# 常に新しい鍵を生成（CI対応）
openssl genpkey -algorithm Ed25519 -out keys/owner_private.pem
openssl pkey -in keys/owner_private.pem -pubout -out keys/owner_public.pem

# review log 作成（この鍵で署名される）
python3 tools/build_review_log.py \
  --source-dir review_records \
  --output-dir out/review_log \
  --private-key keys/owner_private.pem

# 同じ鍵で検証（必ず一致する）
python3 tools/verify_review_log.py \
  --review-log out/review_log/review_log.json \
  --hash-file out/review_log/review_log_hash.txt \
  --sig-file out/review_log/review_log.sig \
  --public-key keys/owner_public.pem

echo "[OK] Stage247 review transparency completed."
