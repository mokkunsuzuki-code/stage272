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
    output_dir = Path("out/release_anchor")
    manifest_path = output_dir / "release_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing file: {manifest_path}")

    manifest = read_json(manifest_path)

    repository = getenv_required("GITHUB_REPOSITORY")
    commit_sha = getenv_required("GITHUB_SHA")
    run_id = getenv_required("GITHUB_RUN_ID")
    run_attempt = getenv_required("GITHUB_RUN_ATTEMPT")
    workflow = getenv_required("GITHUB_WORKFLOW")
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")

    release_receipt = {
        "version": 1,
        "stage": "stage250",
        "release_anchor_type": "github_release_anchor_receipt",
        "release_tag": manifest.get("release_tag"),
        "manifest_sha256": sha256_file(manifest_path),
        "request_sequence": manifest.get("semantic_binding", {}).get("request_sequence"),
        "checkpoint_id": manifest.get("semantic_binding", {}).get("checkpoint_id"),
        "checkpoint_sequence": manifest.get("semantic_binding", {}).get("checkpoint_sequence"),
        "request_sha256": manifest.get("semantic_binding", {}).get("request_sha256"),
        "repository": repository,
        "commit_sha": commit_sha,
        "workflow": workflow,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "run_url": f"{server_url}/{repository}/actions/runs/{run_id}",
        "anchored_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "note": (
            "This receipt records that the release manifest was bound to a public "
            "GitHub Actions execution for release-oriented anchoring."
        ),
    }

    receipt_path = output_dir / "github_release_anchor_receipt.json"
    write_json(receipt_path, release_receipt)

    (output_dir / "github_release_anchor_receipt.sha256").write_text(
        sha256_file(receipt_path) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] wrote: {receipt_path}")
    print(f"[OK] wrote: {output_dir / 'github_release_anchor_receipt.sha256'}")
    print(f"[OK] run_url: {release_receipt['run_url']}")


if __name__ == "__main__":
    main()
