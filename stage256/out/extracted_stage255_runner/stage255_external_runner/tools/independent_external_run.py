#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

STAGE = "stage255"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def candidate_commands(root: Path) -> List[Sequence[str]]:
    candidates: List[Sequence[str]] = []

    env_cmd = os.environ.get("QSP_EXTERNAL_COMMAND", "").strip()
    if env_cmd:
        candidates.append(tuple(shlex.split(env_cmd)))

    shell_candidates = [
        root / "tools" / "run_stage255_qsp.sh",
        root / "tools" / "run_stage254_real_qsp.sh",
        root / "tools" / "run_real_qsp.sh",
        root / "tools" / "run_qsp_demo.sh",
        root / "tools" / "run_stage226_poc.sh",
        root / "verify_all.sh",
    ]

    python_candidates = [
        root / "tools" / "run_stage255_qsp.py",
        root / "tools" / "run_stage254_real_qsp.py",
        root / "tools" / "run_qsp_session.py",
        root / "tools" / "run_minimal_poc.py",
    ]

    for path in shell_candidates:
        if path.exists():
            candidates.append(("bash", str(path)))

    for path in python_candidates:
        if path.exists():
            candidates.append((sys.executable, str(path)))

    return candidates


def run_first_available(root: Path) -> Tuple[List[str], int]:
    attempts = candidate_commands(root)
    if not attempts:
        raise RuntimeError(
            "No QSP entrypoint candidates found. "
            "Set QSP_EXTERNAL_COMMAND to your actual run command."
        )

    last_error: Optional[str] = None

    for cmd in attempts:
        print(f"[INFO] trying command: {' '.join(cmd)}")
        completed = subprocess.run(
            list(cmd),
            cwd=root,
            check=False,
        )
        if completed.returncode == 0:
            return list(cmd), completed.returncode
        last_error = f"command={' '.join(cmd)} returncode={completed.returncode}"

    raise RuntimeError(f"All candidate QSP commands failed. Last error: {last_error}")


def find_result_json(root: Path) -> Path:
    explicit = os.environ.get("QSP_RESULT_JSON", "").strip()
    if explicit:
        path = (root / explicit).resolve() if not Path(explicit).is_absolute() else Path(explicit)
        if path.exists():
            return path
        raise FileNotFoundError(f"QSP_RESULT_JSON does not exist: {path}")

    fixed_candidates = [
        root / "out" / "real_qsp" / "result.json",
        root / "out" / "qsp" / "result.json",
        root / "out" / "qsp_session" / "result.json",
        root / "out" / "session" / "result.json",
        root / "out" / "poc" / "result.json",
    ]

    for path in fixed_candidates:
        if path.exists():
            return path

    dynamic = sorted(
        root.glob("out/**/result.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if dynamic:
        return dynamic[0]

    raise FileNotFoundError("Could not find result.json under out/**/result.json")


def load_manifest_if_present(root: Path) -> Optional[Path]:
    candidates = [
        root / "stage255_bundle_manifest.json",
        root / "out" / "external_runner_bundle" / "stage255_bundle_manifest.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def build_anchor(root: Path, command_used: List[str], result_path: Path) -> Path:
    out_dir = root / "out" / "external_independent"
    out_dir.mkdir(parents=True, exist_ok=True)

    result_copy_path = out_dir / "qsp_result_copy.json"
    shutil.copy2(result_path, result_copy_path)

    manifest_path = load_manifest_if_present(root)
    manifest_sha256 = sha256_file(manifest_path) if manifest_path else None

    anchor = {
        "version": 1,
        "stage": STAGE,
        "type": "external_independent_anchor_request",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "command_used": command_used,
        "qsp_result_path": result_copy_path.relative_to(root).as_posix(),
        "qsp_result_sha256": sha256_file(result_copy_path),
        "bundle_manifest_path": (manifest_path.relative_to(root).as_posix() if manifest_path else None),
        "bundle_manifest_sha256": manifest_sha256,
    }

    anchor_path = out_dir / "anchor_request.json"
    anchor_path.write_text(
        json.dumps(anchor, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    sha_path = out_dir / "anchor_request.json.sha256"
    sha_path.write_text(
        f"{sha256_file(anchor_path)}  {anchor_path.name}\n",
        encoding="utf-8",
    )

    return anchor_path


def main() -> int:
    root = repo_root()

    command_used, _ = run_first_available(root)
    result_path = find_result_json(root)
    anchor_path = build_anchor(root, command_used, result_path)

    print(f"[OK] QSP result found: {result_path}")
    print(f"[OK] anchor generated: {anchor_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
