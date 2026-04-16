#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Motohiro Suzuki

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def getenv_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    anchors_dir = Path("out/anchors")
    request_path = anchors_dir / "anchor_request.json"
    request_sha_path = anchors_dir / "anchor_request.sha256"

    if not request_path.exists():
        raise FileNotFoundError(f"Missing file: {request_path}")
    if not request_sha_path.exists():
        raise FileNotFoundError(f"Missing file: {request_sha_path}")

    request_obj = read_json(request_path)
    request_sha256 = request_sha_path.read_text(encoding="utf-8").strip()

    recomputed_request_sha256 = sha256_file(request_path)
    if request_sha256 != recomputed_request_sha256:
        raise ValueError(
            "anchor_request.sha256 does not match recomputed hash of anchor_request.json"
        )

    repository = getenv_required("GITHUB_REPOSITORY")
    commit_sha = getenv_required("GITHUB_SHA")
    run_id = getenv_required("GITHUB_RUN_ID")
    run_attempt = getenv_required("GITHUB_RUN_ATTEMPT")
    workflow = getenv_required("GITHUB_WORKFLOW")
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")

    anchored_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    receipt = {
        "version": 1,
        "stage": "stage249",
        "anchor_type": "github_actions_external_timestamp_receipt",
        "request_sha256": request_sha256,
        "request_sequence": request_obj.get("sequence"),
        "checkpoint_id": request_obj.get("semantic_binding", {}).get("checkpoint_id"),
        "checkpoint_sequence": request_obj.get("semantic_binding", {}).get("checkpoint_latest_history_sequence"),
        "repository": repository,
        "commit_sha": commit_sha,
        "workflow": workflow,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "run_url": f"{server_url}/{repository}/actions/runs/{run_id}",
        "anchored_at_utc": anchored_at_utc,
        "note": (
            "This receipt records that the anchor request existed in a GitHub Actions "
            "run with externally observable run metadata and UTC execution time."
        ),
    }

    receipt_path = anchors_dir / "github_anchor_receipt.json"
    write_json(receipt_path, receipt)

    (anchors_dir / "github_anchor_receipt.sha256").write_text(
        sha256_file(receipt_path) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] wrote: {receipt_path}")
    print(f"[OK] wrote: {anchors_dir / 'github_anchor_receipt.sha256'}")
    print(f"[OK] run_url: {receipt['run_url']}")


if __name__ == "__main__":
    main()
