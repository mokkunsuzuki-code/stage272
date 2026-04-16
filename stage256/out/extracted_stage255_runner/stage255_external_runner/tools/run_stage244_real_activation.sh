#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/review_packets out/review_status

python3 tools/generate_review_request.py \
  --reviewer-id external-demo \
  --commit demo-commit \
  --repo stage244

python3 tools/verify_review_record.py \
  --input review_records/example_external_review.json | tee out/review_status/review_record_check.txt

echo "[OK] Stage244 real activation artifacts generated"
find out -maxdepth 3 -type f | sort
