#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "verification_score"
OUT_JSON = OUT_DIR / "verification_score.json"
OUT_MD = OUT_DIR / "verification_score.md"


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def safe_read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def round4(value: float) -> float:
    return round(value, 4)


def detect_time_trust(root: Path) -> dict[str, Any]:
    json_candidates = []
    for p in iter_files(root):
        if p.suffix.lower() == ".json":
            json_candidates.append(p)

    confirmations_found = []
    bitcoin_related_files = []

    for p in json_candidates:
        data = safe_read_json(p)
        if data is None:
            continue

        text = json.dumps(data, ensure_ascii=False).lower()
        if "bitcoin" in text or "confirmation" in text or "block height" in text:
            bitcoin_related_files.append(str(p.relative_to(root)))

        def walk(obj: Any):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = str(k).lower()
                    if key in {
                        "bitcoin_confirmations",
                        "confirmations",
                        "btc_confirmations",
                        "confirmation_count",
                    }:
                        if isinstance(v, (int, float)):
                            confirmations_found.append(float(v))
                    walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(data)

    max_confirmations = max(confirmations_found) if confirmations_found else 0.0

    # 6 confirmations を満点基準
    if max_confirmations > 0:
        score = clamp(max_confirmations / 6.0)
        status = "measured"
    elif bitcoin_related_files:
        score = 0.25
        status = "bitcoin-evidence-found-but-confirmations-not-parsed"
    else:
        score = 0.0
        status = "no-bitcoin-evidence-detected"

    return {
        "score": round4(score),
        "status": status,
        "details": {
            "max_confirmations": max_confirmations,
            "bitcoin_related_files": sorted(set(bitcoin_related_files)),
        },
    }


def detect_integrity_trust(root: Path) -> dict[str, Any]:
    sha256_files = []
    ots_files = []

    for p in iter_files(root):
        name = p.name.lower()
        suffix = p.suffix.lower()
        rel = str(p.relative_to(root))

        if suffix == ".ots":
            ots_files.append(rel)

        if suffix == ".sha256" or name.endswith(".sha256.txt") or "sha256" in name:
            sha256_files.append(rel)

    sha_score = 1.0 if sha256_files else 0.0
    ots_score = 1.0 if ots_files else 0.0
    score = (sha_score + ots_score) / 2.0

    status_parts = []
    status_parts.append("sha256:yes" if sha256_files else "sha256:no")
    status_parts.append("ots:yes" if ots_files else "ots:no")

    return {
        "score": round4(score),
        "status": ", ".join(status_parts),
        "details": {
            "sha256_files": sorted(sha256_files),
            "ots_files": sorted(ots_files),
        },
    }


def detect_execution_trust(root: Path) -> dict[str, Any]:
    workflow_files = []
    successful_run_records = []
    run_urls = []

    workflow_dir = root / ".github" / "workflows"
    if workflow_dir.exists():
        for p in workflow_dir.glob("*.yml"):
            workflow_files.append(str(p.relative_to(root)))
        for p in workflow_dir.glob("*.yaml"):
            workflow_files.append(str(p.relative_to(root)))

    for p in iter_files(root):
        if p.name == "actions_runs.json":
            data = safe_read_json(p)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        status = str(item.get("status", "")).lower()
                        conclusion = str(item.get("conclusion", "")).lower()
                        if status == "completed" and conclusion == "success":
                            successful_run_records.append(str(p.relative_to(root)))
                            break

        if p.suffix.lower() == ".json":
            data = safe_read_json(p)
            if data is None:
                continue
            text = json.dumps(data, ensure_ascii=False).lower()
            if "github.com" in text and "/actions/runs/" in text:
                run_urls.append(str(p.relative_to(root)))

    workflow_score = 1.0 if workflow_files else 0.0
    ci_evidence_score = 1.0 if successful_run_records or run_urls else 0.0
    score = (workflow_score + ci_evidence_score) / 2.0

    return {
        "score": round4(score),
        "status": (
            f"workflows:{'yes' if workflow_files else 'no'}, "
            f"ci_evidence:{'yes' if (successful_run_records or run_urls) else 'no'}"
        ),
        "details": {
            "workflow_files": sorted(workflow_files),
            "successful_run_records": sorted(set(successful_run_records)),
            "run_url_evidence_files": sorted(set(run_urls)),
        },
    }


def detect_identity_trust(root: Path) -> dict[str, Any]:
    signature_files = []
    public_key_files = []
    multi_signer_files = []

    for p in iter_files(root):
        rel = str(p.relative_to(root))
        name = p.name.lower()
        suffix = p.suffix.lower()

        if suffix in {".sig", ".asc"}:
            signature_files.append(rel)

        if "public" in name and suffix in {".pem", ".pub", ".asc"}:
            public_key_files.append(rel)

        if name in {"config.yaml", "config.yml"} and "external_signatures" in rel:
            multi_signer_files.append(rel)
        elif "multi" in name and suffix in {".json", ".yaml", ".yml"}:
            multi_signer_files.append(rel)

    signature_score = 1.0 if signature_files else 0.0
    public_key_score = 1.0 if public_key_files else 0.0
    multi_signer_score = 1.0 if multi_signer_files else 0.0

    score = (signature_score + public_key_score + multi_signer_score) / 3.0

    return {
        "score": round4(score),
        "status": (
            f"signatures:{'yes' if signature_files else 'no'}, "
            f"public_keys:{'yes' if public_key_files else 'no'}, "
            f"multi_signer:{'yes' if multi_signer_files else 'no'}"
        ),
        "details": {
            "signature_files": sorted(signature_files),
            "public_key_files": sorted(public_key_files),
            "multi_signer_files": sorted(multi_signer_files),
        },
    }


def build_summary_md(report: dict[str, Any]) -> str:
    c = report["components"]
    lines = [
        "# Stage268 Verification Score",
        "",
        "Stage268 computes a deterministic trust score from four dimensions:",
        "",
        "- Time Trust",
        "- Integrity Trust",
        "- Execution Trust",
        "- Identity Trust",
        "",
        f"**Total Trust:** `{report['total_trust']}`",
        "",
        "## Component Scores",
        "",
        f"- **Time Trust:** `{c['time_trust']['score']}`  ({c['time_trust']['status']})",
        f"- **Integrity Trust:** `{c['integrity_trust']['score']}`  ({c['integrity_trust']['status']})",
        f"- **Execution Trust:** `{c['execution_trust']['score']}`  ({c['execution_trust']['status']})",
        f"- **Identity Trust:** `{c['identity_trust']['score']}`  ({c['identity_trust']['status']})",
        "",
        "## Formula",
        "",
        "`Total Trust = Time × Integrity × Execution × Identity`",
        "",
        "## Important Meaning",
        "",
        "- This is **not** a claim of absolute security.",
        "- This is a **reproducible trust index** based on detected evidence.",
        "- If one component is weak, Total Trust drops multiplicatively.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    time_trust = detect_time_trust(ROOT)
    integrity_trust = detect_integrity_trust(ROOT)
    execution_trust = detect_execution_trust(ROOT)
    identity_trust = detect_identity_trust(ROOT)

    total = (
        time_trust["score"]
        * integrity_trust["score"]
        * execution_trust["score"]
        * identity_trust["score"]
    )

    report = {
        "stage": "stage268",
        "formula": "total_trust = time_trust * integrity_trust * execution_trust * identity_trust",
        "components": {
            "time_trust": time_trust,
            "integrity_trust": integrity_trust,
            "execution_trust": execution_trust,
            "identity_trust": identity_trust,
        },
        "total_trust": round4(total),
    }

    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    OUT_MD.write_text(build_summary_md(report), encoding="utf-8")

    digest = sha256_file(OUT_JSON)
    (OUT_DIR / "verification_score.json.sha256").write_text(
        f"{digest}  verification_score.json\n",
        encoding="utf-8",
    )

    print("[OK] verification score built")
    print(f"[OK] output: {OUT_JSON}")
    print(f"[OK] total_trust: {report['total_trust']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
