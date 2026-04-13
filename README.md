# Stage266: Verified Public Evidence

## Overview

Stage266 introduces **Verified Public Evidence**.

This stage enables:

- Public verification via URL
- Browser-based verification of manifest / receipt / OTS proof
- OpenTimestamps status visibility (pending / confirmed)
- Deterministic verification status published as JSON
- Visual verification state display via GitHub Pages

This transforms:

- "Evidence exists" → "Evidence status is publicly verifiable"

---

## Public Verification URL

👉 https://mokkunsuzuki-code.github.io/stage266/

Anyone can open this URL and verify:

- Manifest file
- Receipt
- OpenTimestamps proof
- Current verification status

---

## What This Stage Proves

- Evidence is publicly accessible via URL
- Verification inputs are reproducible
- OpenTimestamps proof is verifiable
- Verification status is machine-readable (JSON)
- Verification state is human-readable (UI)

---

## OpenTimestamps Status

The page shows:

- pending → waiting for Bitcoin confirmation
- confirmed → anchored in Bitcoin block

When confirmed, it will include:

- block height
- timestamp (UTC)

---

## Architecture

### CI (GitHub Actions)

- Generate release manifest
- Generate receipt
- Stamp with OpenTimestamps
- Upgrade OTS proof
- Verify OTS status
- Generate `verification_status.json`

### GitHub Pages

- Reads `verification_status.json`
- Displays verification state
- Provides public artifact URLs

---

## Key Files


out/release/
├── release_manifest.json
├── release_manifest.json.ots
├── github_actions_receipt.json

docs/
├── index.html
└── status/verification_status.json


---

## Verification Model

This stage separates:

- Evidence generation (CI)
- Evidence verification (OTS)
- Evidence presentation (Pages)

This ensures:

- reproducibility
- transparency
- public verifiability

---

## Important Notes

- "pending" is expected immediately after stamping
- confirmation occurs when Bitcoin anchor is finalized
- verification does not rely on trust in this repository
- anyone can independently verify the proof

---

## Evolution

Stage265:
→ Public verification URL

Stage266:
→ Verification status visibility (this stage)

---

## License

MIT License


---

# Stage268: Verification Score

## Overview

Stage268 introduces a deterministic trust scoring layer on top of the existing evidence system.

This stage evaluates four dimensions:

- Time Trust
- Integrity Trust
- Execution Trust
- Identity Trust

and combines them as:

**Total Trust = Time × Integrity × Execution × Identity**

## What This Stage Adds

- A reproducible trust scoring model
- Machine-generated verification score output
- Local verification script for score consistency
- GitHub Actions workflow that rebuilds and verifies the score

## Output

Generated files:

- `out/verification_score/verification_score.json`
- `out/verification_score/verification_score.json.sha256`
- `out/verification_score/verification_score.md`

## Why This Matters

Earlier stages proved individual trust properties.

Stage268 makes them visible as a unified evaluation model.

This does **not** claim absolute security.

It provides a reproducible evidence-based trust index.

## MIT License

This project is licensed under the MIT License.
