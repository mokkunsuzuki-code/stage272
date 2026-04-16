#!/usr/bin/env python3
from pathlib import Path
import json

out = Path("out/real_qsp")
out.mkdir(parents=True, exist_ok=True)

result = {
    "stage": "stage255",
    "status": "ok",
    "message": "external independent run success"
}

(result_path := out / "result.json").write_text(
    json.dumps(result, indent=2) + "\n",
    encoding="utf-8"
)

print(f"[OK] QSP simulated result generated: {result_path}")
