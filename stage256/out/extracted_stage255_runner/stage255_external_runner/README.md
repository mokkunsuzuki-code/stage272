Stage255: External Independent Execution (QSP)

## Overview

Stage255 introduces **external independent execution** for QSP.

A third party can:

- extract a packaged bundle
- run QSP in their own environment
- generate an anchor request from their own execution result
- verify the anchor locally

This removes dependence on the author's environment and strengthens reproducibility.

---

## Key Concept

Previous stages:

- Author executes QSP
- Author generates anchor

Stage255:

- Third party executes QSP
- Third party generates anchor
- Third party verifies anchor

---

## Quick Start

```bash
git clone https://github.com/mokkunsuzuki-code/stage255.git
cd stage255

bash tools/run_stage255_external_independent.sh
What Happens
Bundle is created
Bundle is extracted
New virtual environment is created
Dependencies are installed
QSP is executed
Anchor is generated
Anchor is verified
Outputs
out/extracted_stage255_runner/stage255_external_runner/out/external_independent/
qsp_result_copy.json
anchor_request.json
anchor_request.json.sha256
Example Anchor
{
  "stage": "stage255",
  "type": "external_independent_anchor_request",
  "command_used": ["python", "tools/run_stage255_qsp.py"],
  "qsp_result_sha256": "...",
  "bundle_manifest_sha256": "..."
}
Security Meaning

This stage upgrades the trust model from:

"Author-generated execution"

to:

"Third-party independently reproducible execution"

It ensures that:

execution is reproducible
results are hash-bound
anchor is locally verifiable
bundle integrity is enforced
Limitations
This does not prove universal correctness
This uses a minimal QSP execution stub
Real-world deployments require further integration
Next Steps
Stage256: External execution logging
Stage257: Multi-party execution chain
License

MIT License