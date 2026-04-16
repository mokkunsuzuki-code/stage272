#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local witness receipt")
    parser.add_argument("--request", required=True, help="Path to multi-anchor request JSON")
    parser.add_argument("--private-key", required=True, help="Ed25519 private key PEM")
    parser.add_argument("--key-id", required=True, help="Logical key id")
    parser.add_argument("--output", required=True, help="Output receipt JSON")
    args = parser.parse_args()

    request_path = Path(args.request)
    private_key_path = Path(args.private_key)
    output_path = Path(args.output)

    request = json.loads(request_path.read_text(encoding="utf-8"))
    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)

    message = request["subject_sha256"].encode("utf-8")
    signature = private_key.sign(message)

    receipt = {
        "version": 1,
        "anchor_type": "local_witness",
        "key_id": args.key_id,
        "public_key_path": str(private_key_path.with_name(private_key_path.name.replace("_private.pem", "_public.pem"))),
        "subject_sha256": request["subject_sha256"],
        "created_at_utc": utc_now(),
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[OK] wrote local witness receipt: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
