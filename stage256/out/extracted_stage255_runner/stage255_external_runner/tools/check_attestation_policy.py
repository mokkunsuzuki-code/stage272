#!/usr/bin/env python3
import json
import os
import sys
from typing import Any, List

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def as_text(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)

def ensure(condition: bool, message: str, checks: List[dict]) -> None:
    checks.append({"ok": bool(condition), "message": message})
    if not condition:
        raise SystemExit(f"[POLICY FAIL] {message}")

def main() -> None:
    if len(sys.argv) != 6:
        print(
            "usage: check_attestation_policy.py "
            "<provenance_json> <sbom_json> <artifact_name> <repo> <signer_workflow>",
            file=sys.stderr,
        )
        sys.exit(2)

    provenance_path = sys.argv[1]
    sbom_path = sys.argv[2]
    artifact_name = sys.argv[3]
    repo = sys.argv[4]
    signer_workflow = sys.argv[5]

    provenance = load_json(provenance_path)
    sbom = load_json(sbom_path)

    prov_text = as_text(provenance)
    sbom_text = as_text(sbom)

    checks: List[dict] = []

    ensure(isinstance(provenance, list) and len(provenance) >= 1,
           "provenance attestation が 1 件以上あること", checks)
    ensure(isinstance(sbom, list) and len(sbom) >= 1,
           "SBOM attestation が 1 件以上あること", checks)

    ensure("https://slsa.dev/provenance/v1" in prov_text,
           "provenance predicate type が SLSA v1 であること", checks)
    ensure("https://spdx.dev/Document/v2.3" in sbom_text,
           "SBOM predicate type が SPDX 2.3 であること", checks)

    ensure(artifact_name in prov_text,
           "provenance attestation が期待した artifact を対象にしていること", checks)
    ensure(artifact_name in sbom_text,
           "SBOM attestation が期待した artifact を対象にしていること", checks)

    ensure(repo in prov_text or repo in sbom_text,
           "repository identity が attestation に現れていること", checks)
    ensure(signer_workflow in prov_text or signer_workflow in sbom_text,
           "signer workflow identity が attestation に現れていること", checks)

    os.makedirs("out/policy", exist_ok=True)
    result = {
        "policy": "stage239-verification-policy",
        "artifact_name": artifact_name,
        "repository": repo,
        "signer_workflow": signer_workflow,
        "checks": checks,
        "result": "pass",
    }

    with open("out/policy/policy_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("[OK] verification policy passed")
    print("[OK] wrote: out/policy/policy_result.json")

if __name__ == "__main__":
    main()
