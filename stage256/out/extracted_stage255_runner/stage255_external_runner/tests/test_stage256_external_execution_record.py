from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_record_script_help() -> None:
    subprocess.run(
        [sys.executable, "tools/record_external_execution.py", "--help"],
        check=True,
    )


def test_verify_script_help() -> None:
    subprocess.run(
        [sys.executable, "tools/verify_external_execution_record.py", "--help"],
        check=True,
    )


def test_doc_exists() -> None:
    assert Path("docs/external_execution_record.md").exists()
