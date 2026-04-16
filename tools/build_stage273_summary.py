#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    reviews = sorted(Path("review_records").glob("*.json"))

    lines = []
    lines.append("# Stage273 Structured Review Context")
    lines.append("")
    lines.append("## Overview")
    lines.append("Stage273 binds review records to SBOM and vulnerability scan artifacts.")
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
            sbom_path = data.get("review_context", {}).get("sbom", {}).get("path", "missing")
            vuln_path = data.get("review_context", {}).get("vulnerability_scan", {}).get("path", "missing")
            lines.append(
                f"- {review_id} | reviewer={reviewer} | result={result} | sbom={sbom_path} | vuln_scan={vuln_path}"
            )

    lines.append("")
    lines.append("## Context Files")
    lines.append("- artifacts/sbom/")
    lines.append("- artifacts/vuln/")
    lines.append("- out/review_context/structured_review_context.json")
    lines.append("- out/review_chain/review_chain_verification.json")
    lines.append("")

    out = Path("out/review_chain/stage273_summary.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
