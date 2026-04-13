#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OTS_PATH = ROOT / "out" / "verification_score" / "verification_score.json.ots"
OUT_DIR = ROOT / "out" / "time_settlement"
OUT_JSON = OUT_DIR / "time_settlement.json"
OUT_MD = OUT_DIR / "time_settlement.md"


def run_command(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not OTS_PATH.exists():
        payload = {
            "stage": "stage270",
            "ots_path": str(OTS_PATH.relative_to(ROOT)),
            "settled": False,
            "confirmations": 0,
            "status": "ots-proof-not-found",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        OUT_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        OUT_MD.write_text("# Stage270 Time Settlement\n\nOTS proof not found.\n", encoding="utf-8")
        print("[INFO] OTS proof not found")
        return 0

    if shutil.which("ots") is None:
        payload = {
            "stage": "stage270",
            "ots_path": str(OTS_PATH.relative_to(ROOT)),
            "settled": False,
            "confirmations": 0,
            "status": "ots-cli-not-installed",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        OUT_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        OUT_MD.write_text("# Stage270 Time Settlement\n\nOTS CLI not installed.\n", encoding="utf-8")
        print("[INFO] OTS CLI not installed")
        return 0

    code, stdout, stderr = run_command(["ots", "upgrade", str(OTS_PATH)])
    combined = (stdout + "\n" + stderr).strip().lower()

    settled = False
    confirmations = 0
    status = "pending"

    if "success" in combined or "upgraded" in combined:
        status = "upgraded"

    if "bitcoin" in combined and ("block" in combined or "attestation" in combined):
        status = "bitcoin-proof-detected"

    if "confirmations" in combined:
        import re
        m = re.search(r"confirmations[^0-9]*([0-9]+)", combined)
        if m:
            confirmations = int(m.group(1))
            if confirmations >= 6:
                settled = True
                status = "settled"
            elif confirmations > 0:
                status = "partially-settled"

    payload = {
        "stage": "stage270",
        "ots_path": str(OTS_PATH.relative_to(ROOT)),
        "settled": settled,
        "confirmations": confirmations,
        "status": status,
        "upgrade_stdout": stdout,
        "upgrade_stderr": stderr,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    OUT_MD.write_text(
        "# Stage270 Time Settlement\n\n"
        f"- Settled: `{settled}`\n"
        f"- Confirmations: `{confirmations}`\n"
        f"- Status: `{status}`\n",
        encoding="utf-8",
    )

    print(f"[INFO] settled: {settled}")
    print(f"[INFO] confirmations: {confirmations}")
    print(f"[INFO] status: {status}")
    print(f"[INFO] output: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
