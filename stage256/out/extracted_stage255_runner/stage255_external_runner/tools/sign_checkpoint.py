import argparse
import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sign_bytes(private_key_path: Path, payload: bytes) -> str:
    key_data = private_key_path.read_bytes()
    private_key = load_pem_private_key(key_data, password=None)
    signature = private_key.sign(payload)
    return base64.b64encode(signature).decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create signed transparency checkpoint")

    parser.add_argument("--merkle-tree", required=True)
    parser.add_argument("--transparency-log", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--output-dir", required=True)

    parser.add_argument("--log-id", default="qsp-transparency-log")
    parser.add_argument("--origin", default="QSP Transparency Log")

    args = parser.parse_args()

    merkle_tree_path = Path(args.merkle_tree)
    transparency_log_path = Path(args.transparency_log)
    private_key_path = Path(args.private_key)
    public_key_path = Path(args.public_key)
    output_dir = Path(args.output_dir)

    merkle_tree = load_json(merkle_tree_path)
    transparency_log = load_json(transparency_log_path)

    root_hash = (
        merkle_tree.get("root_hash")
        or merkle_tree.get("merkle_root")
        or merkle_tree.get("root")
    )

    if not root_hash:
        raise SystemExit("ERROR: merkle_tree.json missing root_hash")

    entries = transparency_log.get("entries", [])
    tree_size = len(entries)

    checkpoint_unsigned = {
        "version": "1.0",
        "type": "signed_transparency_checkpoint",
        "log_id": args.log_id,
        "origin": args.origin,
        "tree_size": tree_size,
        "root_hash": root_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "sha256",
        "signature_algorithm": "ed25519",
    }

    canonical = json.dumps(
        checkpoint_unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    signature_b64 = sign_bytes(private_key_path, canonical)

    public_key_pem = public_key_path.read_text(encoding="utf-8")

    checkpoint_signed = {
        **checkpoint_unsigned,
        "signed_payload_encoding": "json-canonical-sort-keys",
        "signature": signature_b64,
        "public_key_pem": public_key_pem,
    }

    write_json(output_dir / "checkpoint.json", checkpoint_signed)

    write_json(output_dir / "checkpoint_payload.json", checkpoint_unsigned)

    print(f"[OK] wrote: {output_dir / 'checkpoint_payload.json'}")
    print(f"[OK] wrote: {output_dir / 'checkpoint.json'}")
    print(f"[OK] root_hash: {root_hash}")
    print(f"[OK] tree_size: {tree_size}")


if __name__ == "__main__":
    main()