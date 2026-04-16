#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


DEFAULT_INCLUDE_DIRS = [
    "claims",
    "docs",
    "out/checkpoint",
    "out/fail_evidence",
    "out/monitor",
    "out/proofs",
    "out/transparency",
]

DEFAULT_EXCLUDE_PREFIXES = [
    "out/bundle",
    "__pycache__",
    ".pytest_cache",
    ".git",
]

DEFAULT_EXCLUDE_SUFFIXES = [
    ".pyc",
    ".pyo",
    ".DS_Store",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def should_include(path: Path, repo_root: Path) -> bool:
    rel = path.relative_to(repo_root).as_posix()

    for prefix in DEFAULT_EXCLUDE_PREFIXES:
        if rel == prefix or rel.startswith(prefix + "/"):
            return False

    for suffix in DEFAULT_EXCLUDE_SUFFIXES:
        if rel.endswith(suffix):
            return False

    return path.is_file()


def collect_files(repo_root: Path, include_dirs: List[str]) -> List[Path]:
    files: List[Path] = []

    for d in include_dirs:
        base = repo_root / d
        if not base.exists():
            continue
        if base.is_file():
            if should_include(base, repo_root):
                files.append(base)
            continue

        for path in sorted(base.rglob("*")):
            if should_include(path, repo_root):
                files.append(path)

    deduped = sorted(set(files), key=lambda p: p.relative_to(repo_root).as_posix())
    return deduped


def build_file_entries(repo_root: Path, files: List[Path]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for path in files:
        rel = path.relative_to(repo_root).as_posix()
        entries.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return entries


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_private_key(private_key_path: Path) -> Ed25519PrivateKey:
    pem = private_key_path.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("private key is not an Ed25519 private key")
    return key


def main() -> int:
    parser = argparse.ArgumentParser(description="Build signed evidence bundle")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--output-dir", default="out/bundle", help="output directory")
    parser.add_argument(
        "--private-key",
        default="keys/checkpoint_signing_private.pem",
        help="Ed25519 private key PEM",
    )
    parser.add_argument(
        "--bundle-id",
        default="qsp-stage230-signed-evidence-bundle",
        help="bundle identifier",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    private_key_path = (repo_root / args.private_key).resolve()
    if not private_key_path.exists():
        raise FileNotFoundError(f"private key not found: {private_key_path}")

    files = collect_files(repo_root, DEFAULT_INCLUDE_DIRS)
    file_entries = build_file_entries(repo_root, files)

    payload = {
        "bundle_id": args.bundle_id,
        "stage": "stage230",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "file_count": len(file_entries),
        "files": file_entries,
    }

    payload_bytes = canonical_json_bytes(payload)
    payload_sha256 = sha256_bytes(payload_bytes)

    private_key = load_private_key(private_key_path)
    signature = private_key.sign(payload_bytes)

    signature_doc = {
        "algorithm": "Ed25519",
        "payload_sha256": payload_sha256,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }

    summary = {
        "bundle_id": payload["bundle_id"],
        "stage": payload["stage"],
        "file_count": payload["file_count"],
        "payload_sha256": payload_sha256,
        "output_files": [
            "out/bundle/evidence_bundle_payload.json",
            "out/bundle/evidence_bundle_signature.json",
            "out/bundle/evidence_bundle_summary.json",
        ],
    }

    (output_dir / "evidence_bundle_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "evidence_bundle_signature.json").write_text(
        json.dumps(signature_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "evidence_bundle_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] bundle_id: {payload['bundle_id']}")
    print(f"[OK] file_count: {payload['file_count']}")
    print(f"[OK] payload_sha256: {payload_sha256}")
    print(f"[OK] wrote: {output_dir / 'evidence_bundle_payload.json'}")
    print(f"[OK] wrote: {output_dir / 'evidence_bundle_signature.json'}")
    print(f"[OK] wrote: {output_dir / 'evidence_bundle_summary.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
