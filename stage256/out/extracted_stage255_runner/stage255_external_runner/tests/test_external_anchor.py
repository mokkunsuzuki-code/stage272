# MIT License
# Copyright (c) 2025 Motohiro Suzuki

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_generate_anchor_request(tmp_path: Path) -> None:
    transparency = tmp_path / "out" / "transparency"
    anchors = tmp_path / "out" / "anchors"

    history = transparency / "history"
    history.mkdir(parents=True, exist_ok=True)

    write_json(
        transparency / "checkpoint.json",
        {"checkpoint_id": "cp-0002", "sequence": 2},
    )
    write_json(
        history / "checkpoint_0001.json",
        {"checkpoint_id": "cp-0001", "sequence": 1},
    )
    write_json(
        history / "checkpoint_0002.json",
        {"checkpoint_id": "cp-0002", "sequence": 2},
    )
    write_json(
        transparency / "checkpoint_index.json",
        {"entries": [{"sequence": 1}, {"sequence": 2}]},
    )
    (transparency / "root.txt").write_text("abc123\n", encoding="utf-8")

    subprocess.run(
        [
            "python3",
            "tools/generate_anchor_request.py",
            "--transparency-dir",
            str(transparency),
            "--anchors-dir",
            str(anchors),
        ],
        check=True,
    )

    request = json.loads((anchors / "anchor_request.json").read_text(encoding="utf-8"))
    assert request["stage"] == "stage249"
    assert request["sequence"] == 1
    assert request["semantic_binding"]["checkpoint_id"] == "cp-0002"


def test_verify_external_anchor(tmp_path: Path) -> None:
    anchors = tmp_path / "out" / "anchors"
    anchors.mkdir(parents=True, exist_ok=True)

    request = {
        "version": 1,
        "stage": "stage249",
        "sequence": 1,
        "semantic_binding": {
            "checkpoint_id": "cp-0002",
            "checkpoint_latest_history_sequence": 2,
        },
    }
    request_path = anchors / "anchor_request.json"
    write_json(request_path, request)

    import hashlib
    request_sha = hashlib.sha256(request_path.read_bytes()).hexdigest()

    receipt = {
        "version": 1,
        "stage": "stage249",
        "anchor_type": "github_actions_external_timestamp_receipt",
        "request_sha256": request_sha,
        "request_sequence": 1,
        "checkpoint_id": "cp-0002",
        "checkpoint_sequence": 2,
        "run_url": "https://github.com/example/repo/actions/runs/123",
    }
    receipt_path = anchors / "github_anchor_receipt.json"
    write_json(receipt_path, receipt)

    subprocess.run(
        [
            "python3",
            "tools/verify_external_anchor.py",
            "--request",
            str(request_path),
            "--receipt",
            str(receipt_path),
        ],
        check=True,
    )
