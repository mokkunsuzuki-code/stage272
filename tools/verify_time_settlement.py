#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "out" / "time_settlement" / "time_settlement.json"


def main() -> int:
    if not OUT_JSON.exists():
        raise SystemExit("[ERROR] time_settlement.json not found")

    data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    required = {"stage", "ots_path", "settled", "confirmations", "status", "timestamp_utc"}
    missing = required - set(data.keys())
    if missing:
        raise SystemExit(f"[ERROR] missing keys: {sorted(missing)}")

    if not isinstance(data["settled"], bool):
        raise SystemExit("[ERROR] settled is not boolean")

    if not isinstance(data["confirmations"], int):
        raise SystemExit("[ERROR] confirmations is not int")

    print("[OK] time settlement verified")
    print(f"[OK] settled: {data['settled']}")
    print(f"[OK] confirmations: {data['confirmations']}")
    print(f"[OK] status: {data['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
