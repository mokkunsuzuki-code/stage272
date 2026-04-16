from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_stage228_fail_evidence_pipeline(tmp_path: Path) -> None:
    root = tmp_path

    tools_dir = root / "tools"
    out_failures = root / "out" / "failures"
    out_evidence = root / "out" / "fail_evidence"

    tools_dir.mkdir(parents=True)
    out_failures.mkdir(parents=True)
    out_evidence.mkdir(parents=True)

    source_persist = Path("tools/persist_fail_evidence.py").read_text(encoding="utf-8")
    source_verify = Path("tools/verify_fail_evidence.py").read_text(encoding="utf-8")

    (tools_dir / "persist_fail_evidence.py").write_text(source_persist, encoding="utf-8")
    (tools_dir / "verify_fail_evidence.py").write_text(source_verify, encoding="utf-8")

    log_path = out_failures / "attack_fail.log"
    log_path.write_text(
        "[ATTACK] replay_attempt\n"
        "[DETECTED] transcript mismatch\n"
        "[FAIL] session aborted\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            "python3",
            str(tools_dir / "persist_fail_evidence.py"),
            "--input-dir",
            str(out_failures),
            "--output-dir",
            str(out_evidence),
        ],
        check=True,
    )

    index_path = out_evidence / "index.json"
    assert index_path.exists()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["entry_count"] == 1
    assert index["entries"][0]["log_file"].endswith("attack_fail.log")

    subprocess.run(
        [
            "python3",
            str(tools_dir / "verify_fail_evidence.py"),
            "--index",
            str(index_path),
        ],
        check=True,
    )
