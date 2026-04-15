#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def find_stage270_target() -> Path:
    candidates = [
        Path("out/vep/gate_result.json"),
        Path("out/vep/verification_score.json"),
        Path("verification_score.json"),
        Path("gate_result.json"),
        Path("out/gate_result.json"),
        Path("out/verification_score.json"),
    ]
    for c in candidates:
        if c.exists():
            return c

    json_candidates = list(Path(".").rglob("*.json"))
    priority = [p for p in json_candidates if "gate" in p.name.lower() or "verification" in p.name.lower()]
    if priority:
        return priority[0]

    raise FileNotFoundError("Stage270 target artifact not found. Put gate_result.json or verification_score.json in repo.")

def find_previous_review_sha256() -> str:
    chain_dir = Path("out/review_chain")
    chain_dir.mkdir(parents=True, exist_ok=True)
    sha_files = sorted(chain_dir.glob("review_*.sha256"))
    if not sha_files:
        return "GENESIS"
    return sha_files[-1].read_text(encoding="utf-8").strip()

def load_reviewer(reviewer_id: str):
    registry = Path("external_reviewers/reviewer_registry.json")
    data = json.loads(registry.read_text(encoding="utf-8"))
    for r in data.get("reviewers", []):
        if r["id"] == reviewer_id:
            return r
    raise ValueError(f"Reviewer not found: {reviewer_id}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--result", required=True, choices=["accept", "pending", "reject", "comment"])
    parser.add_argument("--comment", required=True)
    parser.add_argument("--stage", default="stage271")
    args = parser.parse_args()

    target = find_stage270_target()
    target_sha = sha256_file(target)
    previous_sha = find_previous_review_sha256()
    reviewer = load_reviewer(args.reviewer_id)

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    review_core = {
        "version": "1",
        "review_id": sha256_text(f"{args.stage}|{reviewer['id']}|{args.result}|{timestamp}")[:16],
        "stage": args.stage,
        "target_artifact": str(target),
        "reviewer": reviewer,
        "review_result": args.result,
        "review_comment": args.comment,
        "timestamp_utc": timestamp,
        "linked_verification": {
            "path": str(target),
            "sha256": target_sha
        },
        "previous_review_sha256": previous_sha
    }

    review_records = Path("review_records")
    review_records.mkdir(parents=True, exist_ok=True)

    out_chain = Path("out/review_chain")
    out_chain.mkdir(parents=True, exist_ok=True)

    review_path = review_records / f"{review_core['review_id']}.json"
    review_text = json.dumps(review_core, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    review_path.write_text(review_text, encoding="utf-8")

    review_sha = sha256_text(review_text)
    sha_path = out_chain / f"review_{review_core['review_id']}.sha256"
    sha_path.write_text(review_sha + "\n", encoding="utf-8")

    latest_path = out_chain / "latest_review_pointer.json"
    latest_path.write_text(
        json.dumps({
            "review_record": str(review_path),
            "sha256": review_sha
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    print(f"[OK] created review record: {review_path}")
    print(f"[OK] review sha256: {review_sha}")
    print(f"[OK] linked target: {target}")
    print(f"[OK] target sha256: {target_sha}")
    print(f"[OK] previous review sha256: {previous_sha}")

if __name__ == "__main__":
    main()
