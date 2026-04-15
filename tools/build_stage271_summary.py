#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    reviews = sorted(Path("review_records").glob("*.json"))
    summary_lines = []
    summary_lines.append("# Stage271 External Review Linked Proof")
    summary_lines.append("")
    summary_lines.append("## Overview")
    summary_lines.append("Stage271 records external review outcomes as verifiable artifacts.")
    summary_lines.append("")
    summary_lines.append("## Review Records")
    if not reviews:
      summary_lines.append("- none")
    else:
      for p in reviews:
        data = json.loads(p.read_text(encoding="utf-8"))
        summary_lines.append(
            f"- {data['review_id']} | reviewer={data['reviewer']['display_name']} | result={data['review_result']} | target={data['target_artifact']}"
        )
    summary_lines.append("")
    summary_lines.append("## Output")
    summary_lines.append("- out/review_chain/review_chain_verification.json")
    summary_lines.append("- out/review_chain/latest_review_pointer.json")
    summary_lines.append("")

    out = Path("out/review_chain/stage271_summary.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
