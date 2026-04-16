#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

from pathlib import Path
import yaml


def main() -> None:
    registry_path = Path("metadata/reviewers/reviewer_registry.yaml")
    if not registry_path.exists():
        raise SystemExit("[FAIL] reviewer registry not found")

    with registry_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    reviewers = data.get("reviewers", [])
    active = [r for r in reviewers if r.get("status") == "active"]

    print(f"[INFO] reviewer count: {len(reviewers)}")
    print(f"[INFO] active reviewer count: {len(active)}")

    if not active:
        raise SystemExit("[FAIL] no active external reviewer registered")

    for reviewer in active:
        key_path = Path(reviewer["key_path"])
        if not key_path.exists():
            raise SystemExit(f"[FAIL] reviewer public key missing: {key_path}")

    print("[OK] active external reviewer registry validated")


if __name__ == "__main__":
    main()
