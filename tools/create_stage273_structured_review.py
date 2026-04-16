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
    parser.add_argument("--sbom", required=True)
    parser.add_argument("--vuln-scan", required=True)
    parser.add_argument("--stage", default="stage273")
    args = parser.parse_args()

    source_file = Path(args.source_file)
    target_artifact = Path(args.target_artifact)
    sbom_file = Path(args.sbom)
    vuln_file = Path(args.vuln_scan)

    for p in [source_file, target_artifact, sbom_file, vuln_file]:
        if not p.exists():
            raise SystemExit(f"Missing required file: {p}")

    reviewer = load_reviewer(args.reviewer_id)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    previous_sha = find_latest_review_sha256()

    source_sha = sha256_file(source_file)
    target_sha = sha256_file(target_artifact)
    sbom_sha = sha256_file(sbom_file)
    vuln_sha = sha256_file(vuln_file)

    review_core = {
        "version": "1",
        "review_id": sha256_text(
            f"{args.stage}|{args.reviewer_id}|{args.result}|{source_sha}|{sbom_sha}|{vuln_sha}|{timestamp}"
        )[:16],
        "stage": args.stage,
        "review_origin": "real_external_review_with_structured_context",
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
        "review_context": {
            "sbom": {
                "path": str(sbom_file),
                "sha256": sbom_sha
            },
            "vulnerability_scan": {
                "path": str(vuln_file),
                "sha256": vuln_sha
            }
        },
        "previous_review_sha256": previous_sha
    }

    normalized_dir = Path("external_reviews/normalized")
    normalized_dir.mkdir(parents=True, exist_ok=True)

    review_records_dir = Path("review_records")
    review_records_dir.mkdir(parents=True, exist_ok=True)

    out_chain = Path("out/review_chain")
    out_chain.mkdir(parents=True, exist_ok=True)

    review_context_dir = Path("out/review_context")
    review_context_dir.mkdir(parents=True, exist_ok=True)

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

    context_summary = {
        "stage": args.stage,
        "review_id": review_core["review_id"],
        "review_source_sha256": source_sha,
        "target_artifact_sha256": target_sha,
        "sbom_sha256": sbom_sha,
        "vulnerability_scan_sha256": vuln_sha
    }
    context_path = review_context_dir / "structured_review_context.json"
    context_path.write_text(
        json.dumps(context_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    print(f"[OK] created normalized review: {normalized_path}")
    print(f"[OK] created review record: {review_path}")
    print(f"[OK] review sha256: {review_sha}")
    print(f"[OK] sbom sha256: {sbom_sha}")
    print(f"[OK] vuln scan sha256: {vuln_sha}")
    print(f"[OK] structured review context: {context_path}")

if __name__ == "__main__":
    main()
