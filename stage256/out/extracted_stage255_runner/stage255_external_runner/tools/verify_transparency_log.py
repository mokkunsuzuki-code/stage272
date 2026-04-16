#!/usr/bin/env python3
# Copyright (c) 2025 Motohiro Suzuki
# Released under the MIT License.

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSPARENCY_DIR = ROOT_DIR / "out" / "transparency"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_history_dir() -> Optional[Path]:
    candidates = [
        TRANSPARENCY_DIR / "history",
        ROOT_DIR / "out" / "checkpoint",
        TRANSPARENCY_DIR / "checkpoints",
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


def entry_leaf_hash(entry: Dict[str, Any]) -> str:
    if "leaf_hash" in entry and isinstance(entry["leaf_hash"], str):
        return entry["leaf_hash"]
    return sha256_hex(canonical_json_bytes(entry))


def merkle_parent(left_hex: str, right_hex: str) -> str:
    return sha256_hex(bytes.fromhex(left_hex) + bytes.fromhex(right_hex))


def build_merkle_root(leaf_hashes: List[str]) -> str:
    if not leaf_hashes:
        return sha256_hex(b"")

    level = leaf_hashes[:]
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(merkle_parent(left, right))
        level = next_level
    return level[0]


def extract_expected_root(
    merkle_obj: Any,
    root_txt_path: Optional[Path],
    checkpoint_obj: Optional[Dict[str, Any]]
) -> Optional[str]:
    if isinstance(merkle_obj, dict):
        for key in ("root", "merkle_root", "root_hash"):
            value = merkle_obj.get(key)
            if isinstance(value, str):
                return value

    if root_txt_path and root_txt_path.exists():
        value = root_txt_path.read_text(encoding="utf-8").strip()
        if value:
            return value

    if isinstance(checkpoint_obj, dict):
        for key in ("root", "merkle_root", "root_hash"):
            value = checkpoint_obj.get(key)
            if isinstance(value, str):
                return value

    return None


def extract_expected_count(log_entries: List[Dict[str, Any]], checkpoint_obj: Optional[Dict[str, Any]]) -> int:
    if isinstance(checkpoint_obj, dict):
        for key in ("entry_count", "entries", "tree_size", "log_size"):
            value = checkpoint_obj.get(key)
            if isinstance(value, int):
                return value
    return len(log_entries)


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


def verify_checkpoint_history(current_root: str, current_count: int) -> None:
    history_dir = resolve_history_dir()
    if history_dir is None:
        print("[WARN] checkpoint history directory not found; skipping history verification")
        return

    checkpoint_files = sorted(history_dir.glob("checkpoint_*.json"))
    if not checkpoint_files:
        print(f"[WARN] no checkpoint_*.json found in {history_dir}; skipping history verification")
        return

    previous_count = -1

    for path in checkpoint_files:
        obj = load_json(path)
        root, count, timestamp = normalize_checkpoint(obj)

        if root is None:
            raise ValueError(f"checkpoint missing root: {path}")
        if count is None:
            raise ValueError(f"checkpoint missing entry count: {path}")

        if count < previous_count:
            raise ValueError(
                f"checkpoint history is not append-only: {path.name} has count {count} < previous {previous_count}"
            )

        previous_count = count
        print(f"[OK] checkpoint {path.name}: entry_count={count}, root={root[:16]}..., timestamp={timestamp or 'n/a'}")

    last_path = checkpoint_files[-1]
    last_obj = load_json(last_path)
    last_root, last_count, _ = normalize_checkpoint(last_obj)

    if last_root != current_root:
        raise ValueError(
            f"latest checkpoint root mismatch: latest history={last_root}, current={current_root}"
        )

    if last_count != current_count:
        raise ValueError(
            f"latest checkpoint entry count mismatch: latest history={last_count}, current={current_count}"
        )

    print("[OK] checkpoint history verified")


def main() -> int:
    try:
        log_path = TRANSPARENCY_DIR / "transparency_log.json"
        merkle_path = TRANSPARENCY_DIR / "merkle_tree.json"
        root_txt_path = TRANSPARENCY_DIR / "root.txt"
        checkpoint_path = TRANSPARENCY_DIR / "checkpoint.json"

        missing = [str(p) for p in [log_path, merkle_path] if not p.exists()]
        if missing:
            raise FileNotFoundError(f"missing required files: {', '.join(missing)}")

        log_obj = load_json(log_path)
        merkle_obj = load_json(merkle_path)
        checkpoint_obj = load_json(checkpoint_path) if checkpoint_path.exists() else None

        entries = get_entries(log_obj)
        leaf_hashes = [entry_leaf_hash(entry) for entry in entries]
        computed_root = build_merkle_root(leaf_hashes)
        expected_root = extract_expected_root(merkle_obj, root_txt_path, checkpoint_obj)
        expected_count = extract_expected_count(entries, checkpoint_obj)

        if expected_root is None:
            raise ValueError("could not determine expected merkle root from merkle_tree.json/root.txt/checkpoint.json")

        if len(entries) != expected_count:
            raise ValueError(
                f"entry count mismatch: log has {len(entries)} entries but checkpoint expects {expected_count}"
            )

        if computed_root != expected_root:
            raise ValueError(f"merkle root mismatch: computed={computed_root} expected={expected_root}")

        print(f"[OK] transparency log loaded: {log_path}")
        print(f"[OK] merkle tree loaded: {merkle_path}")
        print(f"[OK] entry_count: {len(entries)}")
        print(f"[OK] merkle_root: {computed_root}")
        print("[OK] transparency log + Merkle tree verified")

        verify_checkpoint_history(computed_root, len(entries))

        print("[OK] all transparency verification checks passed")
        return 0

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
