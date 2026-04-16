# QSP / Stage273
# Structured Review Context

Stage273 extends Stage272 by structuring what a review is about.

A review record should not only prove that a review happened.
It should also prove which supporting artifacts were in scope.

This stage adds explicit linkage to:

- SBOM
- vulnerability scan results

---

## Why Stage273 matters

Stage272 showed that real external review events could be captured and preserved.

Stage273 makes those reviews more precise.

Instead of saying only:

- a review happened

it can now also say:

- which SBOM was in scope
- which vulnerability scan result was in scope

This makes the review target more explicit and reduces ambiguity.

---

## What is added

- `artifacts/sbom/`
- `artifacts/vuln/`
- structured review context in review records
- `tools/create_stage273_structured_review.py`
- `tools/build_stage273_summary.py`
- `docs/stage273_structured_review_context.md`
- `out/review_context/structured_review_context.json`

---

## Main idea

A verifiable review record becomes stronger when it is explicitly bound to
supply-chain artifacts.

Stage273 binds review records to:

- a verification artifact
- an SBOM
- a vulnerability scan result

---

## Verification

```bash
python3 -m pip install cryptography
python3 tools/verify_stage271_review_chain.py
python3 tools/build_stage273_summary.py
License

MIT License

Copyright (c) 2025 Motohiro Suzuki
