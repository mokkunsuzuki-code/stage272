#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from typing import Any

import yaml


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout


def load_policy(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        print(f"[POLICY FAIL] {message}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: verify_external_policy.py <artifact>")
        sys.exit(2)

    artifact = sys.argv[1]
    policy = load_policy("policy/policy.yaml")

    repo = policy["identity"]["repository"]
    workflow = policy["identity"]["workflow"]
    expected_artifact = policy["artifact"]["name"]
    signer_workflow = f"{repo}/{workflow}"

    ensure(os.path.exists(artifact), f"artifact not found: {artifact}")
    ensure(os.path.basename(artifact) == expected_artifact,
           f"artifact name must be {expected_artifact}")

    os.makedirs("out/external_verification", exist_ok=True)

    print("[INFO] verifying provenance...")
    prov = run(
        f'''gh attestation verify "{artifact}" \
  --repo "{repo}" \
  --signer-workflow "{signer_workflow}" \
  --format json'''
    )

    print("[INFO] verifying sbom...")
    sbom = run(
        f'''gh attestation verify "{artifact}" \
  --repo "{repo}" \
  --signer-workflow "{signer_workflow}" \
  --predicate-type "https://spdx.dev/Document/v2.3" \
  --format json'''
    )

    with open("out/external_verification/provenance.json", "w", encoding="utf-8") as f:
        f.write(prov)

    with open("out/external_verification/sbom.json", "w", encoding="utf-8") as f:
        f.write(sbom)

    result = {
        "policy": "stage240-external-verification-gate",
        "artifact": artifact,
        "repository": repo,
        "workflow": workflow,
        "signer_workflow": signer_workflow,
        "result": "pass",
    }

    with open("out/external_verification/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("[OK] external verification passed")
    print("[OK] wrote: out/external_verification/provenance.json")
    print("[OK] wrote: out/external_verification/sbom.json")
    print("[OK] wrote: out/external_verification/result.json")


if __name__ == "__main__":
    main()
