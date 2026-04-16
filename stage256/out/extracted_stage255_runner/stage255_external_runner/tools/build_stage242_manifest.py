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
    "claims/claims.yaml",
    "docs/security_assumptions.md",
    "docs/threat_model.md",
    "docs/security_claims.md",
    "docs/claim_evidence_mapping.md",
    "docs/stage242_overview.md",
    "evidence_bundle/summary.md",
    "out/ci/actions_runs.json",
    "out/ci/actions_jobs.json",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    selected = []
    for rel in CANDIDATE_FILES:
        path = Path(rel)
        if path.exists() and path.is_file():
            selected.append(
                {
                    "path": rel,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )

    if not selected:
        raise SystemExit("No candidate files found for manifest generation.")

    out_path = Path("out/stage242/release_manifest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "stage": "stage242",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(selected),
        "files": selected,
    }

    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] wrote manifest: {out_path}")


if __name__ == "__main__":
    main()
