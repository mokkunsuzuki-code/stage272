#!/usr/bin/env python3
# Copyright (c) 2025 Motohiro Suzuki
# Released under the MIT License.

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSPARENCY_DIR = ROOT_DIR / "out" / "transparency"
CHECKPOINT_HISTORY_DIR = TRANSPARENCY_DIR / "history"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_checkpoint(obj: dict) -> Tuple[Optional[str], Optional[int]]:
    root = None
    count = None

    for key in ("root", "merkle_root", "root_hash"):
        value = obj.get(key)
        if isinstance(value, str):
            root = value
            break

    for key in ("entry_count", "entries", "tree_size", "log_size"):
        value = obj.get(key)
        if isinstance(value, int):
            count = value
            break

    return root, count


def main() -> int:
    try:
        current_checkpoint = TRANSPARENCY_DIR / "checkpoint.json"
        if not current_checkpoint.exists():
            raise FileNotFoundError(f"missing file: {current_checkpoint}")

        CHECKPOINT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

        current_obj = load_json(current_checkpoint)
        current_root, current_count = normalize_checkpoint(current_obj)

        if current_root is None or current_count is None:
            raise ValueError("checkpoint.json is missing root or entry_count")

        history_files = sorted(CHECKPOINT_HISTORY_DIR.glob("checkpoint_*.json"))

        if history_files:
            latest_path = history_files[-1]
            latest_obj = load_json(latest_path)
            latest_root, latest_count = normalize_checkpoint(latest_obj)

            if latest_root == current_root and latest_count == current_count:
                print(f"[OK] checkpoint history already up to date: {latest_path.name}")
                return 0

            existing_numbers = []
            for path in history_files:
                stem = path.stem  # checkpoint_0001
                try:
                    n = int(stem.split("_")[1])
                    existing_numbers.append(n)
                except (IndexError, ValueError):
                    continue

            next_index = (max(existing_numbers) + 1) if existing_numbers else 1
        else:
            next_index = 1

        new_path = CHECKPOINT_HISTORY_DIR / f"checkpoint_{next_index:04d}.json"
        shutil.copy2(current_checkpoint, new_path)

        print(f"[OK] archived checkpoint: {new_path}")
        print(f"[OK] entry_count: {current_count}")
        print(f"[OK] root: {current_root}")
        return 0

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
