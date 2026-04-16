#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

bash tools/run_stage255_external_independent.sh

python3 tools/record_external_execution.py   --reviewer reviewer_local   --anchor out/extracted_stage255_runner/stage255_external_runner/out/external_independent/anchor_request.json   --manifest out/extracted_stage255_runner/stage255_external_runner/stage255_bundle_manifest.json

python3 tools/verify_external_execution_record.py   --log out/external_execution_record/review_log.json
