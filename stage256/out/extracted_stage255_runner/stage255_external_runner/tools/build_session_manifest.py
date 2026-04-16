#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--session-result",
        default="out/session/qsp_session_result.json",
        help="Path to QSP session result JSON",
    )
    parser.add_argument(
        "--output",
        default="out/session/session_manifest.json",
        help="Path to output session manifest JSON",
    )
    args = parser.parse_args()

    session_result_path = Path(args.session_result)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session_result = json.loads(session_result_path.read_text(encoding="utf-8"))
    session_result_bytes = canonical_json_bytes(session_result)
    session_result_sha256 = sha256_hex(session_result_bytes)

    manifest_core = {
        "schema": "qsp_session_manifest/v1",
        "generated_at": utc_now(),
        "source": {
            "type": "qsp_session_result",
            "path": str(session_result_path),
            "sha256": session_result_sha256,
        },
        "session": {
            "session_id": session_result["session_id"],
            "epoch": session_result["epoch"],
            "handshake_mode": session_result["handshake_mode"],
        },
        "binding": {
            "transcript_hash": session_result["transcript_hash"],
            "policy": session_result["policy"],
            "fail_closed_result": session_result["fail_closed_result"],
        },
        "claims": [
            "This manifest is derived directly from QSP session execution output.",
            "Transcript hash, policy, and fail-closed result are fixed in this manifest.",
            "This manifest is intended to be anchored and independently verified.",
        ],
    }

    manifest_sha256 = sha256_hex(canonical_json_bytes(manifest_core))

    manifest = {
        **manifest_core,
        "manifest_sha256": manifest_sha256,
    }

    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_path.with_suffix(output_path.suffix + ".sha256")).write_text(
        manifest_sha256 + "\n", encoding="utf-8"
    )

    print(f"[OK] wrote: {output_path}")
    print(f"[OK] wrote: {output_path}.sha256")
    print(f"[OK] manifest_sha256: {manifest_sha256}")


if __name__ == "__main__":
    main()
