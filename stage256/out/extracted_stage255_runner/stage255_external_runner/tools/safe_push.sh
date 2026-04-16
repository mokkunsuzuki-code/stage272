#!/usr/bin/env bash
set -euo pipefail

EXPECTED_REPO=$(basename "$(pwd)")
REMOTE_URL=$(git remote get-url origin)

echo "[INFO] Current directory: $EXPECTED_REPO"
echo "[INFO] Remote URL: $REMOTE_URL"

if [[ "$REMOTE_URL" != *"$EXPECTED_REPO.git" ]]; then
  echo "[ERROR] Remote repository does NOT match directory name!"
  echo "[ERROR] Expected: .../$EXPECTED_REPO.git"
  exit 1
fi

echo "[OK] Remote is correct. Proceeding with push."

git push
