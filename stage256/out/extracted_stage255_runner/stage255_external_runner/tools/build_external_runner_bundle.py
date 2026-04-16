#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, tarfile, tempfile

STAGE = "stage255"
SKIP = {".git",".venv",".pytest_cache","__pycache__",".mypy_cache",".ruff_cache","out",".idea",".vscode"}
SKIP_FILES = {".DS_Store"}

RUN_SH = """#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-stage255-external"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
[ -f "${ROOT_DIR}/requirements.txt" ] && pip install -r "${ROOT_DIR}/requirements.txt"
[ -f "${ROOT_DIR}/requirements-dev.txt" ] && pip install -r "${ROOT_DIR}/requirements-dev.txt"
[ -f "${ROOT_DIR}/pyproject.toml" ] && pip install -e "${ROOT_DIR}"
python "${ROOT_DIR}/tools/independent_external_run.py"
python "${ROOT_DIR}/tools/verify_external_anchor.py" --anchor "${ROOT_DIR}/out/external_independent/anchor_request.json" --manifest "${ROOT_DIR}/stage255_bundle_manifest.json"
"""

README = """# Stage255 External Independent Runner

Quick start

```bash
chmod +x run_independent_qsp.sh
./run_independent_qsp.sh
```
"""

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def excluded(path, root):
    rel = path.relative_to(root)
    return path.name in SKIP_FILES or bool(set(rel.parts) & SKIP)

def copy_tree(root, dst):
    for src in root.rglob("*"):
        if excluded(src, root):
            continue
        out = dst / src.relative_to(root)
        if src.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)

def build_manifest(bundle_root):
    files = []
    for p in sorted(bundle_root.rglob("*")):
        if p.is_file():
            files.append({
                "path": p.relative_to(bundle_root).as_posix(),
                "sha256": sha256_file(p),
                "size_bytes": str(p.stat().st_size),
            })
    return {"version":1,"stage":STAGE,"type":"external_independent_runner_bundle","file_count":len(files),"files":files}

def main():
    root = Path(__file__).resolve().parent.parent
    out = root / "out" / "external_runner_bundle"
    out.mkdir(parents=True, exist_ok=True)
    tar_path = out / "stage255_external_runner.tar.gz"
    manifest_copy = out / "stage255_bundle_manifest.json"
    sha_path = out / "stage255_external_runner.tar.gz.sha256"

    with tempfile.TemporaryDirectory() as td:
        bundle = Path(td) / "stage255_external_runner"
        bundle.mkdir()
        copy_tree(root, bundle)
        (bundle / "run_independent_qsp.sh").write_text(RUN_SH, encoding="utf-8")
        os.chmod(bundle / "run_independent_qsp.sh", 0o755)
        (bundle / "EXTERNAL_RUNNER_README.md").write_text(README, encoding="utf-8")
        manifest = build_manifest(bundle)
        manifest_path = bundle / "stage255_bundle_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(bundle, arcname="stage255_external_runner")
        shutil.copy2(manifest_path, manifest_copy)

    tar_sha = sha256_file(tar_path)
    sha_path.write_text(f"{tar_sha}  {tar_path.name}\n", encoding="utf-8")
    print(f"[OK] bundle created: {tar_path}")
    print(f"[OK] manifest copied: {manifest_copy}")
    print(f"[OK] tar sha256: {tar_sha}")

if __name__ == "__main__":
    main()
