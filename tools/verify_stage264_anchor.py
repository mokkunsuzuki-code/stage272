#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sha256_line(path: pathlib.Path) -> tuple[str, str]:
    line = path.read_text(encoding="utf-8").strip()
    parts = line.split()
    if len(parts) < 2:
        raise ValueError(f"invalid sha256 file format: {path}")
    return parts[0], parts[-1].lstrip("*")


def resolve_artifact_path(base: pathlib.Path, manifest_rel: str) -> pathlib.Path:
    manifest_path = pathlib.Path(manifest_rel)

    # downloaded artifact directory を最優先
    candidates = [
        base / manifest_path.name,
        base / manifest_path,
        pathlib.Path.cwd() / manifest_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return (base / manifest_path.name).resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="out/release",
        help="directory containing release_manifest.json and related files",
    )
    parser.add_argument(
        "--ots-bin",
        default="",
        help="path to ots command (optional)",
    )
    args = parser.parse_args()

    base = pathlib.Path(args.dir).resolve()
    manifest = base / "release_manifest.json"
    manifest_sha = base / "release_manifest.json.sha256"
    manifest_ots = base / "release_manifest.json.ots"
    receipt = base / "github_actions_receipt.json"

    required = [manifest, manifest_sha, manifest_ots, receipt]
    for p in required:
        if not p.exists():
            print(f"[ERROR] missing required file: {p}")
            sys.exit(1)

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))

    artifacts = manifest_data.get("artifacts", [])
    if not artifacts:
        print("[ERROR] manifest has no artifacts")
        sys.exit(1)

    for artifact in artifacts:
        manifest_rel = artifact["path"]
        artifact_path = resolve_artifact_path(base, manifest_rel)
        expected_sha = artifact["sha256"]

        if not artifact_path.exists():
            print(f"[ERROR] missing artifact referenced by manifest: {manifest_rel}")
            print(f"        looked for: {artifact_path}")
            sys.exit(1)

        actual_sha = sha256_file(artifact_path)
        if actual_sha != expected_sha:
            print(f"[ERROR] artifact sha256 mismatch: {manifest_rel}")
            print(f"        resolved:  {artifact_path}")
            print(f"        expected:  {expected_sha}")
            print(f"        actual:    {actual_sha}")
            sys.exit(1)

        print(f"[OK] artifact verified: {manifest_rel}")
        print(f"[OK] resolved path: {artifact_path}")
        print(f"[OK] sha256: {actual_sha}")

    expected_manifest_sha, filename = load_sha256_line(manifest_sha)
    actual_manifest_sha = sha256_file(manifest)

    if filename != manifest.name:
        print(f"[ERROR] sha256 sidecar filename mismatch: expected {manifest.name}, found {filename}")
        sys.exit(1)

    if expected_manifest_sha != actual_manifest_sha:
        print("[ERROR] release_manifest.json sha256 mismatch")
        print(f"        expected: {expected_manifest_sha}")
        print(f"        actual:   {actual_manifest_sha}")
        sys.exit(1)

    print(f"[OK] manifest verified: {manifest}")
    print(f"[OK] manifest_sha256: {actual_manifest_sha}")

    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    run_url = receipt_data.get("github_actions", {}).get("run_url", "")
    if run_url:
        print(f"[OK] GitHub Actions run_url: {run_url}")
    else:
        print("[WARN] GitHub Actions run_url not present")

    ots_bin = args.ots_bin.strip()
    if ots_bin:
        try:
            result = subprocess.run(
                [ots_bin, "verify", str(manifest_ots)],
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                print("[OK] ots verify succeeded")
                if result.stdout.strip():
                    print(result.stdout.strip())
            else:
                print("[WARN] ots verify did not fully succeed yet")
                if result.stdout.strip():
                    print(result.stdout.strip())
                if result.stderr.strip():
                    print(result.stderr.strip())
                print("[WARN] This can happen before the proof is upgraded/finalized.")
        except FileNotFoundError:
            print(f"[WARN] ots binary not found: {ots_bin}")
    else:
        print("[INFO] ots verification skipped (no --ots-bin supplied)")

    print("[OK] Stage264 anchor structure verified")


if __name__ == "__main__":
    main()
