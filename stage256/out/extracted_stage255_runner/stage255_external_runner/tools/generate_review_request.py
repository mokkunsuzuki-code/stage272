#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

DEFAULT_ARTIFACTS = [
    "README.md",
    "docs/external_reviewer_policy.md",
    "docs/reviewer_scope.md",
    "docs/reviewer_quickstart.md",
    "docs/review_verdict_levels.md",
    "review_records/template_review_record.json",
    "review_records/example_external_review.json"
]

def build_packet(reviewer_id: str, commit: str, repo: str) -> dict:
    return {
        "version": 1,
        "stage": "Stage244",
        "title": "Real External Reviewer Activation",
        "repository": repo,
        "reviewer_id": reviewer_id,
        "reviewed_commit": commit,
        "objective": "Provide a bounded and reproducible activation path for a real external reviewer.",
        "scope_documents": [
            "docs/external_reviewer_policy.md",
            "docs/reviewer_scope.md",
            "docs/review_verdict_levels.md"
        ],
        "artifacts": DEFAULT_ARTIFACTS,
        "verification_steps": [
            "python3 tools/generate_review_request.py --reviewer-id <id> --commit <commit> --repo <repo>",
            "python3 tools/verify_review_record.py --input review_records/example_external_review.json"
        ],
        "expected_outputs": [
            "out/review_packets/review_request.json",
            "out/review_packets/review_request.md",
            "[OK] review record is valid"
        ],
        "allowed_verdicts": [
            "observed",
            "reproduced",
            "reviewed",
            "approved"
        ]
    }

def write_markdown(packet: dict, path: Path) -> None:
    lines = [
        "# Review Request Packet",
        "",
        f"- Stage: {packet['stage']}",
        f"- Title: {packet['title']}",
        f"- Repository: {packet['repository']}",
        f"- Reviewer ID: {packet['reviewer_id']}",
        f"- Reviewed Commit: {packet['reviewed_commit']}",
        "",
        "## Objective",
        "",
        packet["objective"],
        "",
        "## Scope Documents",
        ""
    ]
    for item in packet["scope_documents"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Review Artifacts", ""])
    for item in packet["artifacts"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Verification Steps", ""])
    for step in packet["verification_steps"]:
        lines.append(f"- `{step}`")

    lines.extend(["", "## Expected Outputs", ""])
    for output in packet["expected_outputs"]:
        lines.append(f"- {output}")

    lines.extend(["", "## Allowed Verdicts", ""])
    for verdict in packet["allowed_verdicts"]:
        lines.append(f"- {verdict}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage244 review request packet")
    parser.add_argument("--reviewer-id", required=True, help="Reviewer identifier")
    parser.add_argument("--commit", required=True, help="Reviewed commit")
    parser.add_argument("--repo", default="stage244", help="Repository name")
    args = parser.parse_args()

    out_dir = Path("out/review_packets")
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = build_packet(args.reviewer_id, args.commit, args.repo)

    json_path = out_dir / "review_request.json"
    md_path = out_dir / "review_request.md"

    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(packet, md_path)

    print(f"[OK] wrote: {json_path}")
    print(f"[OK] wrote: {md_path}")

if __name__ == "__main__":
    main()
