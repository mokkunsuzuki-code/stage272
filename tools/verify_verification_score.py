#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "verification_score"
OUT_JSON = OUT_DIR / "verification_score.json"
OUT_SHA256 = OUT_DIR / "verification_score.json.sha256"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not OUT_JSON.exists():
        raise SystemExit("[ERROR] verification_score.json not found")

    if not OUT_SHA256.exists():
        raise SystemExit("[ERROR] verification_score.json.sha256 not found")

    data = json.loads(OUT_JSON.read_text(encoding="utf-8"))

    required_top = {"stage", "formula", "components", "total_trust"}
    missing_top = required_top - set(data.keys())
    if missing_top:
        raise SystemExit(f"[ERROR] missing top-level keys: {sorted(missing_top)}")

    components = data["components"]
    required_components = {
        "time_trust",
        "integrity_trust",
        "execution_trust",
        "identity_trust",
    }
    missing_components = required_components - set(components.keys())
    if missing_components:
        raise SystemExit(f"[ERROR] missing component keys: {sorted(missing_components)}")

    for key in required_components:
        score = components[key]["score"]
        if not isinstance(score, (int, float)):
            raise SystemExit(f"[ERROR] {key}.score is not numeric")
        if score < 0 or score > 1:
            raise SystemExit(f"[ERROR] {key}.score is outside [0,1]")

    expected_total = round(
        components["time_trust"]["score"]
        * components["integrity_trust"]["score"]
        * components["execution_trust"]["score"]
        * components["identity_trust"]["score"],
        4,
    )

    actual_total = data["total_trust"]
    if round(actual_total, 4) != expected_total:
        raise SystemExit(
            f"[ERROR] total_trust mismatch: expected {expected_total}, got {actual_total}"
        )

    actual_digest = sha256_file(OUT_JSON)
    sha_line = OUT_SHA256.read_text(encoding="utf-8").strip()
    expected_digest = sha_line.split()[0]

    if actual_digest != expected_digest:
        raise SystemExit(
            f"[ERROR] sha256 mismatch: expected {expected_digest}, got {actual_digest}"
        )

    print("[OK] verification score verified")
    print(f"[OK] total_trust: {actual_total}")
    print(f"[OK] sha256: {actual_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
