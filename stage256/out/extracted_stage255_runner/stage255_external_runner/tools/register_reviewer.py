#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--contact", required=True)
    parser.add_argument("--key-path", required=True)
    parser.add_argument("--key-fingerprint", required=True)
    parser.add_argument("--status", default="active")
    parser.add_argument("--scope", nargs="+", default=["release_manifest", "approval_policy"])
    args = parser.parse_args()

    registry_path = Path("metadata/reviewers/reviewer_registry.yaml")
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if registry_path.exists():
        with registry_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {"version": 1, "reviewers": []}

    reviewers = data.setdefault("reviewers", [])

    for existing in reviewers:
        if existing.get("reviewer_id") == args.reviewer_id:
            raise SystemExit(f"[FAIL] reviewer already exists: {args.reviewer_id}")

    reviewers.append(
        {
            "reviewer_id": args.reviewer_id,
            "display_name": args.display_name,
            "contact": args.contact,
            "key_path": args.key_path,
            "key_fingerprint": args.key_fingerprint,
            "status": args.status,
            "scope": args.scope,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    with registry_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"[OK] registered reviewer: {args.reviewer_id}")


if __name__ == "__main__":
    main()
