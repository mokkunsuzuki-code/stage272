from __future__ import annotations

import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_review_log import build_review_log
from tools.verify_review_log import verify_review_log


def write_test_keypair(private_key_path: Path, public_key_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def write_review_record(path: Path, review_id: str, decision: str) -> None:
    payload = {
        "review_id": review_id,
        "reviewer_id": "tester",
        "reviewer_type": "external",
        "timestamp": "2026-04-01T00:00:00Z",
        "subject": f"subject-{review_id}",
        "decision": decision,
        "summary": f"summary-{review_id}",
        "evidence_refs": ["README.md"],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_and_verify_review_log(tmp_path: Path) -> None:
    review_dir = tmp_path / "review_records"
    out_dir = tmp_path / "out" / "review_log"
    key_dir = tmp_path / "keys"

    review_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    key_dir.mkdir(parents=True)

    write_review_record(review_dir / "review_001.json", "RVW-001", "accepted")
    write_review_record(review_dir / "review_002.json", "RVW-002", "implemented")

    private_key_path = key_dir / "owner_private.pem"
    public_key_path = key_dir / "owner_public.pem"
    write_test_keypair(private_key_path, public_key_path)

    result = build_review_log(review_dir, out_dir, private_key_path)
    assert result["review_count"] == 2

    verify = verify_review_log(
        out_dir / "review_log.json",
        out_dir / "review_log_hash.txt",
        out_dir / "review_log.sig",
        public_key_path,
    )
    assert verify["signature_verified"] is True
    assert verify["review_count"] == 2


def test_verify_detects_tampering(tmp_path: Path) -> None:
    review_dir = tmp_path / "review_records"
    out_dir = tmp_path / "out" / "review_log"
    key_dir = tmp_path / "keys"

    review_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    key_dir.mkdir(parents=True)

    write_review_record(review_dir / "review_001.json", "RVW-001", "accepted")
    write_review_record(review_dir / "review_002.json", "RVW-002", "implemented")

    private_key_path = key_dir / "owner_private.pem"
    public_key_path = key_dir / "owner_public.pem"
    write_test_keypair(private_key_path, public_key_path)

    build_review_log(review_dir, out_dir, private_key_path)

    review_log_path = out_dir / "review_log.json"
    payload = json.loads(review_log_path.read_text(encoding="utf-8"))
    payload["entries"][0]["decision"] = "tampered"
    review_log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        verify_review_log(
            review_log_path,
            out_dir / "review_log_hash.txt",
            out_dir / "review_log.sig",
            public_key_path,
        )
        assert False, "tampering should have been detected"
    except RuntimeError as exc:
        assert "hash mismatch" in str(exc) or "leaf hash mismatch" in str(exc)
