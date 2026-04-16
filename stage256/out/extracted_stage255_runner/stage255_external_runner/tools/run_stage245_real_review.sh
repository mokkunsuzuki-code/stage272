#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/review_packets out/review_status out/review_signed

python3 tools/generate_review_request.py \
  --reviewer-id external-simulated-reviewer \
  --commit stage245-demo-commit \
  --repo stage245

python3 tools/verify_review_record.py \
  --input review_records/real_review_record.json | tee out/review_status/review_record_check.txt

python3 tools/sign_review_record.py \
  --input review_records/real_review_record.json \
  --signature-output review_records/real_review_record.sig | tee out/review_signed/sign_review_record.txt

python3 tools/verify_signed_review_record.py \
  --input review_records/real_review_record.json \
  --signature review_records/real_review_record.sig | tee out/review_signed/verify_signed_review_record.txt

echo "[OK] Stage245 real review record flow completed"
find out -maxdepth 3 -type f | sort
