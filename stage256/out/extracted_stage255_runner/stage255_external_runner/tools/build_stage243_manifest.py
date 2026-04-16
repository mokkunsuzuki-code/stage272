#!/usr/bin/env python3
"""
MIT License © 2025 Motohiro Suzuki
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


CANDIDATE_FILES = [
    "README.md",
    "docs/stage243_policy.yaml",
    "docs/reviewer_onboarding.md",
    "docs/reviewer_invitation_template.md",
    "metadata/reviewers/reviewer_registry.yaml",
    "claims/claims.yaml",
    "docs/security_assumptions.md",
    "docs/threat_model.md",
    "docs/security_claims.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    files = []
    for rel in CANDIDATE_FILES:
        path = Path(rel)
        if path.exists() and path.is_file():
            files.append(
                {
                    "path": rel,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )

    if not files:
        raise SystemExit("No files found for stage243 manifest.")

    out_path = Path("out/stage243/release_manifest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "stage": "stage243",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }

    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] wrote manifest: {out_path}")


if __name__ == "__main__":
    main()
