#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE_JSON = ROOT / "out" / "vep_status" / "gate_result.json"
TIME_JSON = ROOT / "out" / "time_settlement" / "time_settlement.json"


def main() -> int:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        print("[INFO] GITHUB_STEP_SUMMARY not set")
        return 0

    if not GATE_JSON.exists():
        print("[INFO] gate_result.json not found")
        return 0

    gate = json.loads(GATE_JSON.read_text(encoding="utf-8"))
    time_data = {}
    if TIME_JSON.exists():
        time_data = json.loads(TIME_JSON.read_text(encoding="utf-8"))

    decision = gate.get("decision")
    scores = gate.get("scores", {})

    lines = []
    lines.append("# Stage270 Settlement Status")
    lines.append("")

    if decision == "accept":
        lines.append("## ✅ ACCEPT")
        lines.append("")
        lines.append("Time settlement completed. VEP decision has been promoted from pending to accept.")
    elif decision == "pending":
        lines.append("## ⏳ PENDING")
        lines.append("")
        lines.append("Immediate gate passed, but Bitcoin time settlement is still pending.")
    else:
        lines.append("## ❌ REJECT")
        lines.append("")
        lines.append("Trust gate rejected the release due to incomplete trust conditions.")

    lines.append("")
    lines.append("### Scores")
    lines.append("")
    lines.append(f"- Time Trust: `{scores.get('time_trust')}`")
    lines.append(f"- Integrity Trust: `{scores.get('integrity_trust')}`")
    lines.append(f"- Execution Trust: `{scores.get('execution_trust')}`")
    lines.append(f"- Identity Trust: `{scores.get('identity_trust')}`")
    lines.append(f"- Immediate Score: `{scores.get('immediate_score')}`")
    lines.append(f"- Total Trust: `{scores.get('total_trust')}`")
    lines.append("")
    lines.append("### Time Settlement")
    lines.append("")
    lines.append(f"- Settled: `{time_data.get('settled')}`")
    lines.append(f"- Confirmations: `{time_data.get('confirmations')}`")
    lines.append(f"- Status: `{time_data.get('status')}`")

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("[OK] step summary written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
