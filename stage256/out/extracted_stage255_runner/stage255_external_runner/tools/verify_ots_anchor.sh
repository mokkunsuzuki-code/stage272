#!/usr/bin/env bash
set -e

FILE="$1"

ots verify "$FILE.ots"

echo "[OK] OTS verified"
