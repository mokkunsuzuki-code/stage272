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


def find_latest_checkpoint(history_dir: Path) -> Path:
    candidates = sorted(history_dir.glob("checkpoint_[0-9][0-9][0-9][0-9].json"))
    if not candidates:
        raise FileNotFoundError(
            f"No checkpoint history files found in: {history_dir}"
        )
    return candidates[-1]


def next_sequence(history_dir: Path) -> int:
    candidates = sorted(history_dir.glob("request_[0-9][0-9][0-9][0-9].json"))
    if not candidates:
        return 1
    latest = candidates[-1].stem.split("_")[-1]
    return int(latest) + 1


def canonical_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external timestamp anchor request")
    parser.add_argument(
        "--transparency-dir",
        default="out/transparency",
        help="Directory containing transparency outputs",
    )
    parser.add_argument(
        "--anchors-dir",
        default="out/anchors",
        help="Directory where anchor request files will be written",
    )
    args = parser.parse_args()

    transparency_dir = Path(args.transparency_dir)
    anchors_dir = Path(args.anchors_dir)
    history_dir = anchors_dir / "history"

    checkpoint_current = transparency_dir / "checkpoint.json"
    checkpoint_history_dir = transparency_dir / "history"
    checkpoint_index = transparency_dir / "checkpoint_index.json"
    root_txt = transparency_dir / "root.txt"

    if not checkpoint_current.exists():
        raise FileNotFoundError(f"Missing file: {checkpoint_current}")
    if not checkpoint_index.exists():
        raise FileNotFoundError(f"Missing file: {checkpoint_index}")
    if not root_txt.exists():
        raise FileNotFoundError(f"Missing file: {root_txt}")

    latest_checkpoint = find_latest_checkpoint(checkpoint_history_dir)

    seq = next_sequence(history_dir)
    request_name = f"request_{seq:04d}.json"
    request_path = history_dir / request_name

    previous_request_sha256 = None
    if seq > 1:
        previous_path = history_dir / f"request_{seq - 1:04d}.json"
        if previous_path.exists():
            previous_request_sha256 = sha256_file(previous_path)

    current_checkpoint_obj = read_json(checkpoint_current)
    latest_checkpoint_obj = read_json(latest_checkpoint)

    request_core = {
        "version": 1,
        "stage": "stage249",
        "anchor_type": "external_timestamp_anchor_request",
        "sequence": seq,
        "previous_request_sha256": previous_request_sha256,
        "targets": {
            "checkpoint_current": {
                "path": str(checkpoint_current),
                "sha256": sha256_file(checkpoint_current),
            },
            "checkpoint_latest_history": {
                "path": str(latest_checkpoint),
                "sha256": sha256_file(latest_checkpoint),
            },
            "checkpoint_index": {
                "path": str(checkpoint_index),
                "sha256": sha256_file(checkpoint_index),
            },
            "root_txt": {
                "path": str(root_txt),
                "sha256": sha256_file(root_txt),
                "value": root_txt.read_text(encoding="utf-8").strip(),
            },
        },
        "semantic_binding": {
            "checkpoint_current_sequence": current_checkpoint_obj.get("sequence"),
            "checkpoint_latest_history_sequence": latest_checkpoint_obj.get("sequence"),
            "checkpoint_id": latest_checkpoint_obj.get("checkpoint_id"),
        },
        "note": (
            "This request binds the latest transparency checkpoint state to a future "
            "externally observable timestamp anchor receipt."
        ),
    }

    write_json(request_path, request_core)

    request_sha256 = sha256_file(request_path)
    anchor_request_path = anchors_dir / "anchor_request.json"
    write_json(anchor_request_path, request_core)

    (anchors_dir / "anchor_request.sha256").write_text(
        request_sha256 + "\n",
        encoding="utf-8",
    )

    index_path = anchors_dir / "anchor_index.json"
    if index_path.exists():
        index_data = read_json(index_path)
    else:
        index_data = {
            "version": 1,
            "stage": "stage249",
            "entries": [],
        }

    index_data["entries"].append(
        {
            "sequence": seq,
            "request_file": str(request_path),
            "request_sha256": request_sha256,
            "checkpoint_sequence": latest_checkpoint_obj.get("sequence"),
            "checkpoint_id": latest_checkpoint_obj.get("checkpoint_id"),
            "root_sha256": request_core["targets"]["root_txt"]["sha256"],
        }
    )

    write_json(index_path, index_data)

    summary = {
        "request_file": str(request_path),
        "anchor_request_file": str(anchor_request_path),
        "request_sha256": request_sha256,
        "sequence": seq,
        "checkpoint_sequence": latest_checkpoint_obj.get("sequence"),
        "checkpoint_id": latest_checkpoint_obj.get("checkpoint_id"),
        "root_value": request_core["targets"]["root_txt"]["value"],
    }
    write_json(anchors_dir / "anchor_summary.json", summary)

    print(f"[OK] wrote: {request_path}")
    print(f"[OK] wrote: {anchor_request_path}")
    print(f"[OK] wrote: {anchors_dir / 'anchor_request.sha256'}")
    print(f"[OK] wrote: {index_path}")
    print(f"[OK] request_sha256: {request_sha256}")


if __name__ == "__main__":
    main()
