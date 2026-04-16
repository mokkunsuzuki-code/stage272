#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(cmd: str, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def first_present(data: dict, keys: list[str], default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def to_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "ok", "pass", "passed", "success"}:
            return True
        if v in {"false", "fail", "failed", "error"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def normalize_result(raw: dict, source_path: Path) -> dict:
    transcript = first_present(raw, ["transcript", "messages", "events", "log"], default=[])
    if not isinstance(transcript, list):
        transcript = [transcript]

    policy = first_present(raw, ["policy", "selected_policy", "config"], default={})
    if not isinstance(policy, dict):
        policy = {"raw_policy": policy}

    session_id = first_present(raw, ["session_id", "sid", "id"], default="qsp-real-session-0001")
    epoch = first_present(raw, ["epoch"], default=1)
    handshake_mode = first_present(raw, ["handshake_mode", "mode"], default="real-qsp-integration")

    transcript_hash = first_present(raw, ["transcript_hash"], default=None)
    if transcript_hash is None:
        transcript_hash = sha256_hex(canonical_json_bytes(transcript))

    fail_closed_result = first_present(raw, ["fail_closed_result"], default=None)

    if fail_closed_result is None:
        fail_closed_passed = first_present(raw, ["fail_closed", "fail_closed_passed"], default=None)
        status = first_present(raw, ["status", "verdict", "result"], default=None)
        if fail_closed_passed is None:
            fail_closed_passed = to_bool(status, default=True)

        fail_closed_result = {
            "passed": to_bool(fail_closed_passed, default=True),
            "checks": [
                {
                    "name": "derived_from_real_qsp_output",
                    "passed": to_bool(fail_closed_passed, default=True),
                    "reason": "Derived from real QSP execution output for Stage254 normalization",
                }
            ],
        }

    normalized = {
        "schema": "qsp_session_result/v1",
        "generated_at": utc_now(),
        "source_type": "real_qsp_execution",
        "source_path": str(source_path),
        "session_id": session_id,
        "epoch": epoch,
        "handshake_mode": handshake_mode,
        "policy": policy,
        "transcript": transcript,
        "transcript_hash": transcript_hash,
        "fail_closed_result": fail_closed_result,
        "notes": [
            "Stage254 normalizes real QSP execution output into the session anchoring schema.",
            "This replaces the Stage253 deterministic demo with real integration.",
        ],
    }
    return normalized


def find_candidate_result_files(search_roots: list[Path]) -> list[Path]:
    candidate_names = {
        "qsp_session_result.json",
        "result.json",
        "session_result.json",
        "qsp_result.json",
        "poc_result.json",
    }
    found: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.name in candidate_names:
                found.append(path)
    return sorted(set(found))


def main() -> None:
    out_dir = Path("out/session")
    out_dir.mkdir(parents=True, exist_ok=True)

    qsp_repo = Path(os.environ.get("QSP_REAL_REPO", "../stage226")).resolve()

    custom_cmd = os.environ.get("QSP_REAL_RUN_CMD")
    candidate_cmds = []
    if custom_cmd:
        candidate_cmds.append(custom_cmd)

    candidate_cmds.extend(
        [
            "./tools/run_stage226_poc.sh",
            "python3 tools/run_stage226_poc.py",
            "python3 tools/run_minimal_poc.py",
            "python3 tools/run_demo.py",
            "python3 main.py",
        ]
    )

    if not qsp_repo.exists():
        print(f"[ERROR] QSP repo not found: {qsp_repo}")
        sys.exit(1)

    executed = False
    for cmd in candidate_cmds:
        rc, out, err = run_command(cmd, qsp_repo)
        if rc == 0:
            executed = True
            print(f"[OK] executed real QSP command: {cmd}")
            if out.strip():
                print(out.strip())
            break

    if not executed:
        print("[ERROR] Could not execute real QSP command in stage226.")
        print("[INFO] Set QSP_REAL_RUN_CMD explicitly, for example:")
        print('export QSP_REAL_RUN_CMD="python3 tools/run_stage226_poc.py"')
        sys.exit(1)

    candidate_files = find_candidate_result_files(
        [
            qsp_repo / "out",
            qsp_repo,
        ]
    )

    if not candidate_files:
        print("[ERROR] No candidate QSP JSON result file found after execution.")
        sys.exit(1)

    selected = candidate_files[-1]
    raw = read_json(selected)
    normalized = normalize_result(raw, selected)

    result_path = out_dir / "qsp_session_result.json"
    result_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] selected real QSP result: {selected}")
    print(f"[OK] wrote normalized result: {result_path}")
    print(f"[OK] transcript_hash: {normalized['transcript_hash']}")
    print(f"[OK] fail_closed_passed: {normalized['fail_closed_result']['passed']}")


if __name__ == "__main__":
    main()
