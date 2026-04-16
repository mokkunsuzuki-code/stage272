#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/failures
mkdir -p out/fail_evidence

cat > out/failures/downgrade_fail.log << 'LOG'
[ATTACK] downgrade_attempt
[DETECTED] protocol parameter mismatch
[FAIL] session aborted by fail-closed policy
[RESULT] evidence must be persisted
LOG

python3 tools/persist_fail_evidence.py \
  --input-dir out/failures \
  --output-dir out/fail_evidence

python3 tools/verify_fail_evidence.py \
  --index out/fail_evidence/index.json

echo "[OK] Stage228 fail evidence persistence completed"
