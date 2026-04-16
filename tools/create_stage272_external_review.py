#!/usr/bin/env python3
import argparse
import hashlib
import json
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

def find_latest_review_sha256() -> str:
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
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--result", required=True, choices=["accept", "pending", "reject", "comment"])
    parser.add_argument("--comment", required=True)
    parser.add_argument("--target-artifact", default="out/verification_score/verification_score.json")
    parser.add_argument("--stage", default="stage272")
    args = parser.parse_args()

    source_file = Path(args.source_file)
    target_artifact = Path(args.target_artifact)

    if not source_file.exists():
        raise SystemExit(f"Missing source file: {source_file}")
    if not target_artifact.exists():
        raise SystemExit(f"Missing target artifact: {target_artifact}")

    reviewer = load_reviewer(args.reviewer_id)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    previous_sha = find_latest_review_sha256()

    source_sha = sha256_file(source_file)
    target_sha = sha256_file(target_artifact)

    review_core = {
        "version": "1",
        "review_id": sha256_text(
            f"{args.stage}|{args.reviewer_id}|{args.result}|{source_sha}|{timestamp}"
        )[:16],
        "stage": args.stage,
        "review_origin": "real_external_review",
        "review_source": {
            "path": str(source_file),
            "sha256": source_sha
        },
        "target_artifact": str(target_artifact),
        "reviewer": reviewer,
        "review_result": args.result,
        "review_comment": args.comment,
        "timestamp_utc": timestamp,
        "linked_verification": {
            "path": str(target_artifact),
            "sha256": target_sha
        },
        "previous_review_sha256": previous_sha
    }

    normalized_dir = Path("external_reviews/normalized")
    normalized_dir.mkdir(parents=True, exist_ok=True)

    review_records_dir = Path("review_records")
    review_records_dir.mkdir(parents=True, exist_ok=True)

    out_chain = Path("out/review_chain")
    out_chain.mkdir(parents=True, exist_ok=True)

    normalized_path = normalized_dir / f"{review_core['review_id']}.normalized.json"
    normalized_text = json.dumps(review_core, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    normalized_path.write_text(normalized_text, encoding="utf-8")

    review_path = review_records_dir / f"{review_core['review_id']}.json"
    review_path.write_text(normalized_text, encoding="utf-8")

    review_sha = sha256_text(normalized_text)
    sha_path = out_chain / f"review_{review_core['review_id']}.sha256"
    sha_path.write_text(review_sha + "\n", encoding="utf-8")

    pointer = {
        "review_record": str(review_path),
        "normalized_record": str(normalized_path),
        "sha256": review_sha
    }
    (out_chain / "latest_review_pointer.json").write_text(
        json.dumps(pointer, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    evidence = {
        "stage": args.stage,
        "review_id": review_core["review_id"],
        "review_source_path": str(source_file),
        "review_source_sha256": source_sha,
        "target_artifact_path": str(target_artifact),
        "target_artifact_sha256": target_sha,
        "result": args.result
    }
    evidence_path = Path("out/external_review_evidence") / "review_001_evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    print(f"[OK] created normalized review: {normalized_path}")
    print(f"[OK] created review record: {review_path}")
    print(f"[OK] source sha256: {source_sha}")
    print(f"[OK] target sha256: {target_sha}")
    print(f"[OK] review sha256: {review_sha}")
    print(f"[OK] previous review sha256: {previous_sha}")
    print(f"[OK] evidence written: {evidence_path}")

if __name__ == "__main__":
    main()
