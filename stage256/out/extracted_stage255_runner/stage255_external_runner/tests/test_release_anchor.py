# MIT License
# Copyright (c) 2025 Motohiro Suzuki

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_generate_release_manifest(tmp_path: Path) -> None:
    anchors = tmp_path / "out" / "anchors"
    release_anchor = tmp_path / "out" / "release_anchor"
    anchors.mkdir(parents=True, exist_ok=True)

    request = {
        "version": 1,
        "stage": "stage249",
        "sequence": 1,
        "semantic_binding": {
            "checkpoint_id": 1,
            "checkpoint_latest_history_sequence": None,
        },
    }
    write_json(anchors / "anchor_request.json", request)
    (anchors / "anchor_request.sha256").write_text("dummy-sha\n", encoding="utf-8")
    write_json(
        anchors / "anchor_summary.json",
        {
            "request_sha256": "abc123",
            "checkpoint_id": 1,
            "checkpoint_sequence": None,
            "sequence": 1,
        },
    )

    subprocess.run(
        [
            "python3",
            "tools/generate_release_manifest.py",
            "--anchors-dir",
            str(anchors),
            "--output-dir",
            str(release_anchor),
            "--release-tag",
            "stage250-v1",
        ],
        check=True,
    )

    manifest = json.loads((release_anchor / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "stage250"
    assert manifest["release_tag"] == "stage250-v1"
    assert manifest["semantic_binding"]["checkpoint_id"] == 1


def test_verify_release_anchor(tmp_path: Path) -> None:
    release_anchor = tmp_path / "out" / "release_anchor"
    release_anchor.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": 1,
        "stage": "stage250",
        "release_tag": "stage250-v1",
        "semantic_binding": {
            "request_sequence": 1,
            "checkpoint_id": 1,
            "checkpoint_sequence": None,
            "request_sha256": "abc123",
        },
    }
    manifest_path = release_anchor / "release_manifest.json"
    write_json(manifest_path, manifest)

    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    receipt = {
        "version": 1,
        "stage": "stage250",
        "release_anchor_type": "github_release_anchor_receipt",
        "release_tag": "stage250-v1",
        "manifest_sha256": manifest_sha256,
        "request_sequence": 1,
        "checkpoint_id": 1,
        "checkpoint_sequence": None,
        "request_sha256": "abc123",
        "run_url": "https://github.com/example/repo/actions/runs/123",
    }
    receipt_path = release_anchor / "github_release_anchor_receipt.json"
    write_json(receipt_path, receipt)

    subprocess.run(
        [
            "python3",
            "tools/verify_release_anchor.py",
            "--manifest",
            str(manifest_path),
            "--receipt",
            str(receipt_path),
        ],
        check=True,
    )
