"""
MIT License © 2025 Motohiro Suzuki
"""

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(cmd, expect_success=True):
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed:\n{' '.join(cmd)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )
    if not expect_success and result.returncode == 0:
        raise AssertionError(
            f"Command unexpectedly succeeded:\n{' '.join(cmd)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )
    return result


def clean():
    shutil.rmtree(ROOT / "signatures", ignore_errors=True)
    shutil.rmtree(ROOT / "out" / "stage242", ignore_errors=True)
    (ROOT / "signatures").mkdir(parents=True, exist_ok=True)
    (ROOT / "out" / "stage242").mkdir(parents=True, exist_ok=True)


def test_stage242_requires_external_reviewer():
    clean()

    run(["python3", "tools/generate_stage242_keys.py"])
    run(["python3", "tools/build_stage242_manifest.py"])
    run([
        "python3", "tools/sign_stage242_artifact.py",
        "--config", "docs/stage242_policy.yaml",
        "--signer-id", "developer",
    ])
    run([
        "python3", "tools/sign_stage242_artifact.py",
        "--config", "docs/stage242_policy.yaml",
        "--signer-id", "auditor",
    ])

    result = run([
        "python3", "tools/verify_stage242_threshold.py",
        "--config", "docs/stage242_policy.yaml",
        "--signatures-dir", "signatures",
    ], expect_success=False)

    combined = result.stdout + result.stderr
    assert "independence group policy not met" in combined


def test_stage242_passes_with_developer_and_external_reviewer():
    clean()

    run(["python3", "tools/generate_stage242_keys.py"])
    run(["python3", "tools/build_stage242_manifest.py"])
    run([
        "python3", "tools/sign_stage242_artifact.py",
        "--config", "docs/stage242_policy.yaml",
        "--signer-id", "developer",
    ])
    run([
        "python3", "tools/sign_stage242_artifact.py",
        "--config", "docs/stage242_policy.yaml",
        "--signer-id", "reviewer",
    ])

    result = run([
        "python3", "tools/verify_stage242_threshold.py",
        "--config", "docs/stage242_policy.yaml",
        "--signatures-dir", "signatures",
    ], expect_success=True)

    assert "[OK] stage242 policy satisfied" in result.stdout
