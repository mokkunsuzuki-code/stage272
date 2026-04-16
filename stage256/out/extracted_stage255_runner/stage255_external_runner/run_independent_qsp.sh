#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-stage255-external"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
[ -f "${ROOT_DIR}/requirements.txt" ] && pip install -r "${ROOT_DIR}/requirements.txt"
[ -f "${ROOT_DIR}/requirements-dev.txt" ] && pip install -r "${ROOT_DIR}/requirements-dev.txt"
[ -f "${ROOT_DIR}/pyproject.toml" ] && pip install -e "${ROOT_DIR}"
python "${ROOT_DIR}/tools/independent_external_run.py"
python "${ROOT_DIR}/tools/verify_external_anchor.py" --anchor "${ROOT_DIR}/out/external_independent/anchor_request.json" --manifest "${ROOT_DIR}/stage255_bundle_manifest.json"
