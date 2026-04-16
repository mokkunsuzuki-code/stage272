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
    shutil.rmtree(ROOT / "out" / "stage243", ignore_errors=True)
    (ROOT / "out" / "stage243").mkdir(parents=True, exist_ok=True)
    (ROOT / "metadata" / "reviewers").mkdir(parents=True, exist_ok=True)
    (ROOT / "keys").mkdir(parents=True, exist_ok=True)


def test_stage243_fails_without_active_reviewer():
    clean()

    (ROOT / "metadata" / "reviewers" / "reviewer_registry.yaml").write_text(
        "version: 1\n\nreviewers: []\n",
        encoding="utf-8",
    )

    result = run(
        ["python3", "tools/verify_stage243_registry.py"],
        expect_success=False,
    )

    combined = result.stdout + result.stderr
    assert "no active external reviewer registered" in combined


def test_stage243_passes_with_active_reviewer():
    clean()

    (ROOT / "keys" / "reviewer_example_public.pem").write_text(
        "-----BEGIN PUBLIC KEY-----\n"
        "MCowBQYDK2VwAyEA1111111111111111111111111111111111111111111=\n"
        "-----END PUBLIC KEY-----\n",
        encoding="utf-8",
    )

    run([
        "python3", "tools/register_reviewer.py",
        "--reviewer-id", "reviewer_example",
        "--display-name", "Example Reviewer",
        "--contact", "example@example.com",
        "--key-path", "keys/reviewer_example_public.pem",
        "--key-fingerprint", "SHA256:examplefingerprint",
        "--status", "active",
        "--scope", "release_manifest", "approval_policy",
    ])

    result = run(
        ["python3", "tools/verify_stage243_registry.py"],
        expect_success=True,
    )

    assert "[OK] active external reviewer registry validated" in result.stdout
