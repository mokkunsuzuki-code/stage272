#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

python3 tools/build_external_runner_bundle.py

rm -rf out/extracted_stage255_runner
mkdir -p out/extracted_stage255_runner

tar -xzf out/external_runner_bundle/stage255_external_runner.tar.gz -C out/extracted_stage255_runner

cd out/extracted_stage255_runner/stage255_external_runner
chmod +x run_independent_qsp.sh
./run_independent_qsp.sh
