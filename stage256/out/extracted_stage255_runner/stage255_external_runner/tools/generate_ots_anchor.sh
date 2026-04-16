#!/usr/bin/env bash
set -e

FILE="$1"

if [ ! -f "$FILE" ]; then
  echo "[ERROR] file not found: $FILE"
  exit 1
fi

ots stamp "$FILE"

echo "[OK] OTS created: ${FILE}.ots"
