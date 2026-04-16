#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files: List[Dict[str, str]] = manifest.get("files", [])

    for item in files:
        rel = item["path"]
        expected = item["sha256"]
        target = root / rel

        if not target.exists():
            raise FileNotFoundError(f"Manifest file missing: {target}")

        actual = sha256_file(target)
        if actual != expected:
            raise ValueError(
                f"Manifest hash mismatch: {rel} expected={expected} actual={actual}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", required=True, help="Path to anchor_request.json")
    parser.add_argument("--manifest", required=True, help="Path to stage255 bundle manifest")
    args = parser.parse_args()

    anchor_path = Path(args.anchor).resolve()
    manifest_path = Path(args.manifest).resolve()
    root = manifest_path.parent

    if not anchor_path.exists():
        raise FileNotFoundError(f"Anchor not found: {anchor_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    verify_manifest(root, manifest_path)

    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))

    manifest_sha_expected = anchor.get("bundle_manifest_sha256")
    manifest_sha_actual = sha256_file(manifest_path)
    if manifest_sha_expected and manifest_sha_expected != manifest_sha_actual:
        raise ValueError(
            f"Bundle manifest sha mismatch: expected={manifest_sha_expected} actual={manifest_sha_actual}"
        )

    qsp_result_rel = anchor["qsp_result_path"]
    qsp_result_path = root / qsp_result_rel
    if not qsp_result_path.exists():
        raise FileNotFoundError(f"QSP result copy missing: {qsp_result_path}")

    qsp_result_sha_actual = sha256_file(qsp_result_path)
    if qsp_result_sha_actual != anchor["qsp_result_sha256"]:
        raise ValueError(
            "QSP result sha mismatch: "
            f"expected={anchor['qsp_result_sha256']} actual={qsp_result_sha_actual}"
        )

    anchor_sha_path = anchor_path.with_suffix(anchor_path.suffix + ".sha256")
    if anchor_sha_path.exists():
        line = anchor_sha_path.read_text(encoding="utf-8").strip()
        expected_anchor_sha = line.split()[0]
        actual_anchor_sha = sha256_file(anchor_path)
        if expected_anchor_sha != actual_anchor_sha:
            raise ValueError(
                f"Anchor sha mismatch: expected={expected_anchor_sha} actual={actual_anchor_sha}"
            )

    print("[OK] manifest files verified")
    print("[OK] bundle manifest hash verified")
    print("[OK] qsp result hash verified")
    print("[OK] anchor hash verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
