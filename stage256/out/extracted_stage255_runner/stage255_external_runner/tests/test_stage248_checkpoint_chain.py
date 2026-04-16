from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def checkpoint_files(history_dir: Path):
    return sorted(history_dir.glob("checkpoint_[0-9][0-9][0-9][0-9].json"))


def test_stage248_checkpoint_chain_roundtrip() -> None:
    history_dir = ROOT / "out" / "review_log_history"
    if history_dir.exists():
        for p in history_dir.glob("*"):
            p.unlink()

    result = subprocess.run(
        ["bash", "tools/run_stage248_checkpoint_chain.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    cps = checkpoint_files(history_dir)
    assert len(cps) >= 1

    latest = json.loads(cps[-1].read_text(encoding="utf-8"))
    assert latest["checkpoint_id"] >= 1
    assert "checkpoint_hash" in latest
    assert "signature" in latest


def test_stage248_detects_checkpoint_tampering() -> None:
    history_dir = ROOT / "out" / "review_log_history"
    if history_dir.exists():
        for p in history_dir.glob("*"):
            p.unlink()

    run = subprocess.run(
        ["bash", "tools/run_stage248_checkpoint_chain.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + "\n" + run.stderr

    checkpoint_file = checkpoint_files(history_dir)[-1]
    payload = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    payload["review_count"] = 999999
    checkpoint_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    verify = subprocess.run(
        [
            "python3",
            "tools/verify_checkpoint_chain.py",
            "--history-dir",
            "out/review_log_history",
            "--public-key",
            "keys/owner_public.pem",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify.returncode != 0
