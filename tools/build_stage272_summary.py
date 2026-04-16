#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    reviews = sorted(Path("review_records").glob("*.json"))

    lines = []
    lines.append("# Stage272 Real External Review Integration")
    lines.append("")
    lines.append("## Overview")
    lines.append("Stage272 integrates at least one real external review into the verifiable review chain.")
    lines.append("")
    lines.append("## Review Records")

    if not reviews:
        lines.append("- none")
    else:
        for p in reviews:
            data = json.loads(p.read_text(encoding="utf-8"))
            review_id = data.get("review_id", p.stem)
            reviewer = data.get("reviewer", {}).get("display_name", "unknown")
            result = data.get("review_result", "unknown")
            origin = data.get("review_origin", "unknown")
            target = data.get("target_artifact", "unknown")
            lines.append(
                f"- {review_id} | reviewer={reviewer} | result={result} | origin={origin} | target={target}"
            )

    lines.append("")
    lines.append("## Evidence")
    lines.append("- external_reviews/raw/")
    lines.append("- external_reviews/normalized/")
    lines.append("- out/external_review_evidence/review_001_evidence.json")
    lines.append("- out/review_chain/review_chain_verification.json")
    lines.append("")

    out = Path("out/review_chain/stage272_summary.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
