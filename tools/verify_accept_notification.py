#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "out" / "notifications" / "accept_notification.json"


def main() -> int:
    if not OUT_JSON.exists():
        print("[INFO] accept_notification.json not found (this is normal unless decision=accept)")
        return 0

    data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    required = {"stage", "event", "message", "decision", "scores", "time_settlement", "timestamp_utc"}
    missing = required - set(data.keys())
    if missing:
        raise SystemExit(f"[ERROR] missing keys: {sorted(missing)}")

    if data["decision"] != "accept":
        raise SystemExit("[ERROR] accept_notification exists but decision is not accept")

    print("[OK] accept notification verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
