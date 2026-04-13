#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE_JSON = ROOT / "out" / "vep_status" / "gate_result.json"
TIME_JSON = ROOT / "out" / "time_settlement" / "time_settlement.json"
OUT_DIR = ROOT / "out" / "notifications"
OUT_JSON = OUT_DIR / "accept_notification.json"
OUT_MD = OUT_DIR / "accept_notification.md"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not GATE_JSON.exists():
        print("[INFO] gate_result.json not found")
        return 0

    gate = json.loads(GATE_JSON.read_text(encoding="utf-8"))
    time_data = {}
    if TIME_JSON.exists():
        time_data = json.loads(TIME_JSON.read_text(encoding="utf-8"))

    decision = gate.get("decision")
    if decision != "accept":
        print("[INFO] decision is not accept; no accept notification generated")
        return 0

    payload = {
        "stage": "stage270",
        "event": "accept",
        "message": "Time settlement completed. VEP decision promoted to accept.",
        "decision": decision,
        "reason": gate.get("reason"),
        "scores": gate.get("scores", {}),
        "time_settlement": {
            "settled": time_data.get("settled"),
            "confirmations": time_data.get("confirmations"),
            "status": time_data.get("status"),
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    OUT_MD.write_text(
        "# Stage270 Accept Notification\n\n"
        "## Status\n\n"
        "**ACCEPT**\n\n"
        "## Meaning\n\n"
        "Time settlement completed. Pending has been promoted to accept.\n\n"
        "## Scores\n\n"
        f"- Time Trust: `{payload['scores'].get('time_trust')}`\n"
        f"- Integrity Trust: `{payload['scores'].get('integrity_trust')}`\n"
        f"- Execution Trust: `{payload['scores'].get('execution_trust')}`\n"
        f"- Identity Trust: `{payload['scores'].get('identity_trust')}`\n"
        f"- Immediate Score: `{payload['scores'].get('immediate_score')}`\n"
        f"- Total Trust: `{payload['scores'].get('total_trust')}`\n\n"
        "## Time Settlement\n\n"
        f"- Settled: `{payload['time_settlement'].get('settled')}`\n"
        f"- Confirmations: `{payload['time_settlement'].get('confirmations')}`\n"
        f"- Status: `{payload['time_settlement'].get('status')}`\n",
        encoding="utf-8",
    )

    print(f"[OK] accept notification written: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
