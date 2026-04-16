from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_stage230_signed_bundle_roundtrip():
    repo_root = Path(__file__).resolve().parents[1]

    run = subprocess.run(
        ["bash", "tools/run_stage230_signed_bundle.sh"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "[OK] Stage230 signed evidence bundle complete" in run.stdout

    payload_path = repo_root / "out/bundle/evidence_bundle_payload.json"
    signature_path = repo_root / "out/bundle/evidence_bundle_signature.json"
    summary_path = repo_root / "out/bundle/evidence_bundle_summary.json"

    assert payload_path.exists()
    assert signature_path.exists()
    assert summary_path.exists()

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert payload["stage"] == "stage230"
    assert payload["file_count"] == len(payload["files"])
    assert summary["file_count"] == payload["file_count"]
    assert payload["file_count"] > 0
