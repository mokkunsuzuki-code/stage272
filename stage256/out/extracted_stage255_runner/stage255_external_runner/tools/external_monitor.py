#!/usr/bin/env python3
# Copyright (c) 2025 Motohiro Suzuki
# Released under the MIT License.

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSPARENCY_DIR = ROOT_DIR / "out" / "transparency"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_history_dir() -> Optional[Path]:
    candidates = [
        TRANSPARENCY_DIR / "history",
        ROOT_DIR / "out" / "checkpoint",
        ROOT_DIR / "out" / "transparency" / "checkpoints",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return None


def get_entries(log_obj: Any) -> List[Dict[str, Any]]:
    if isinstance(log_obj, list):
        return log_obj
    if isinstance(log_obj, dict):
        if isinstance(log_obj.get("entries"), list):
            return log_obj["entries"]
        if isinstance(log_obj.get("log"), list):
            return log_obj["log"]
    raise ValueError("Could not find log entries in transparency_log.json")


def normalize_checkpoint(obj: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    root = None
    count = None
    timestamp = None

    for key in ("root", "merkle_root", "root_hash"):
        if isinstance(obj.get(key), str):
            root = obj[key]
            break

    for key in ("entry_count", "entries", "tree_size", "log_size"):
        if isinstance(obj.get(key), int):
            count = obj[key]
            break

    for key in ("timestamp", "created_at", "generated_at"):
        if isinstance(obj.get(key), str):
            timestamp = obj[key]
            break

    return root, count, timestamp


def main() -> int:
    try:
        log_path = TRANSPARENCY_DIR / "transparency_log.json"
        merkle_path = TRANSPARENCY_DIR / "merkle_tree.json"
        root_path = TRANSPARENCY_DIR / "root.txt"
        checkpoint_path = TRANSPARENCY_DIR / "checkpoint.json"

        if not log_path.exists():
            raise FileNotFoundError(f"missing file: {log_path}")
        if not merkle_path.exists():
            raise FileNotFoundError(f"missing file: {merkle_path}")

        log_obj = load_json(log_path)
        _ = load_json(merkle_path)
        entries = get_entries(log_obj)

        root = root_path.read_text(encoding="utf-8").strip() if root_path.exists() else None
        checkpoint_root = None
        checkpoint_count = None
        checkpoint_timestamp = None

        if checkpoint_path.exists():
            checkpoint_obj = load_json(checkpoint_path)
            checkpoint_root, checkpoint_count, checkpoint_timestamp = normalize_checkpoint(checkpoint_obj)

        history_dir = resolve_history_dir()
        history_files = sorted(history_dir.glob("checkpoint_*.json")) if history_dir else []

        print("[external_monitor] transparency status")
        print(f"  log_path           : {log_path}")
        print(f"  merkle_path        : {merkle_path}")
        print(f"  entry_count        : {len(entries)}")
        print(f"  root_txt           : {root or 'n/a'}")
        print(f"  checkpoint_root    : {checkpoint_root or 'n/a'}")
        print(f"  checkpoint_count   : {checkpoint_count if checkpoint_count is not None else 'n/a'}")
        print(f"  checkpoint_time    : {checkpoint_timestamp or 'n/a'}")
        print(f"  checkpoint_history : {len(history_files)} file(s)")

        if history_files:
            print("  history_files:")
            for p in history_files:
                print(f"    - {p.name}")

        print("[OK] external monitor completed")
        return 0

    except Exception as e:
        print(f"[ERROR] external monitor failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
