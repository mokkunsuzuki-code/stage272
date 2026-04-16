#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Motohiro Suzuki

from __future__ import annotations

import argparse
import hashlib
import json
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage250 release anchor manifest")
    parser.add_argument(
        "--anchors-dir",
        default="out/anchors",
        help="Directory containing Stage249 anchor outputs",
    )
    parser.add_argument(
        "--output-dir",
        default="out/release_anchor",
        help="Directory to write release anchor outputs",
    )
    parser.add_argument(
        "--release-tag",
        default="stage250-v1",
        help="Logical release tag for the release manifest",
    )
    args = parser.parse_args()

    anchors_dir = Path(args.anchors_dir)
    output_dir = Path(args.output_dir)

    anchor_request = anchors_dir / "anchor_request.json"
    anchor_request_sha = anchors_dir / "anchor_request.sha256"
    anchor_summary = anchors_dir / "anchor_summary.json"

    if not anchor_request.exists():
        raise FileNotFoundError(f"Missing file: {anchor_request}")
    if not anchor_request_sha.exists():
        raise FileNotFoundError(f"Missing file: {anchor_request_sha}")
    if not anchor_summary.exists():
        raise FileNotFoundError(f"Missing file: {anchor_summary}")

    request_obj = read_json(anchor_request)
    summary_obj = read_json(anchor_summary)

    manifest = {
        "version": 1,
        "stage": "stage250",
        "release_anchor_type": "release_manifest",
        "release_tag": args.release_tag,
        "sources": {
            "anchor_request": {
                "path": str(anchor_request),
                "sha256": sha256_file(anchor_request),
            },
            "anchor_request_sha256_file": {
                "path": str(anchor_request_sha),
                "sha256": sha256_file(anchor_request_sha),
                "value": anchor_request_sha.read_text(encoding="utf-8").strip(),
            },
            "anchor_summary": {
                "path": str(anchor_summary),
                "sha256": sha256_file(anchor_summary),
            },
        },
        "semantic_binding": {
            "request_sequence": request_obj.get("sequence"),
            "checkpoint_id": request_obj.get("semantic_binding", {}).get("checkpoint_id"),
            "checkpoint_sequence": request_obj.get("semantic_binding", {}).get("checkpoint_latest_history_sequence"),
            "request_sha256": summary_obj.get("request_sha256"),
        },
        "note": (
            "This manifest binds Stage249 anchor artifacts into a release-oriented "
            "public anchoring unit for Stage250."
        ),
    }

    manifest_path = output_dir / "release_manifest.json"
    write_json(manifest_path, manifest)

    (output_dir / "release_manifest.sha256").write_text(
        sha256_file(manifest_path) + "\n",
        encoding="utf-8",
    )

    summary = {
        "release_tag": args.release_tag,
        "manifest_file": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "request_sequence": manifest["semantic_binding"]["request_sequence"],
        "checkpoint_id": manifest["semantic_binding"]["checkpoint_id"],
        "request_sha256": manifest["semantic_binding"]["request_sha256"],
    }
    write_json(output_dir / "release_manifest_summary.json", summary)

    print(f"[OK] wrote: {manifest_path}")
    print(f"[OK] wrote: {output_dir / 'release_manifest.sha256'}")
    print(f"[OK] wrote: {output_dir / 'release_manifest_summary.json'}")
    print(f"[OK] release_tag: {args.release_tag}")
    print(f"[OK] manifest_sha256: {summary['manifest_sha256']}")


if __name__ == "__main__":
    main()
