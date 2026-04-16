#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "attacks"
WORK_DIR = OUT_DIR / "workspace"
REPORT_PATH = OUT_DIR / "attack_report.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

def copy_target(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def tamper_file(path: Path):
    with path.open("a", encoding="utf-8") as f:
        f.write("\n# tampered by attack simulation\n")

def evaluate_integrity(original: Path, copied: Path) -> bool:
    return sha256_file(original) == sha256_file(copied)

def main():
    scenarios_path = ROOT / "attacks" / "attack_scenarios.json"
    if not scenarios_path.exists():
        print(f"[ERROR] missing: {scenarios_path}")
        sys.exit(1)

    ensure_dirs()

    with scenarios_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    overall_success = True

    for scenario in data.get("scenarios", []):
        scenario_id = scenario["id"]
        scenario_type = scenario["type"]
        target = scenario["target"]
        expected = scenario["expected_result"]

        result = {
            "id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"],
            "type": scenario_type,
            "target": target,
            "expected_result": expected,
            "observed_result": None,
            "success": False
        }

        if scenario_type == "baseline":
            result["observed_result"] = "pass"
            result["success"] = (expected == "pass")
            results.append(result)
            if not result["success"]:
                overall_success = False
            continue

        original = ROOT / target
        copied = WORK_DIR / target

        if not original.exists():
            result["observed_result"] = "error_missing_target"
            result["success"] = False
            results.append(result)
            overall_success = False
            continue

        copy_target(original, copied)
        tamper_file(copied)

        same = evaluate_integrity(original, copied)

        observed = "pass" if same else "fail"
        result["observed_result"] = observed
        result["success"] = (observed == expected)

        results.append(result)
        if not result["success"]:
            overall_success = False

    report = {
        "stage": "Stage227",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "scenario_count": len(results),
            "passed": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "overall_success": overall_success
        },
        "results": results
    }

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[OK] wrote: {REPORT_PATH}")
    print(f"[OK] overall_success: {overall_success}")

    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()
