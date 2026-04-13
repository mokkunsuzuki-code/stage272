# Stage268 Verification Score Model

Stage268 introduces a deterministic trust evaluation model.

## Purpose

Previous stages produced evidence, signatures, timestamps, and CI verification.

Stage268 turns those into a visible and reproducible score:

- Time Trust
- Integrity Trust
- Execution Trust
- Identity Trust

## Formula

Total Trust = Time × Integrity × Execution × Identity

## Meaning of Each Component

### 1. Time Trust
Evidence of external time anchoring, especially Bitcoin confirmations.

### 2. Integrity Trust
Evidence that artifacts are content-bound and tamper-detectable:
- SHA256
- OpenTimestamps (.ots)

### 3. Execution Trust
Evidence that the system was actually executed and checked:
- GitHub Actions workflows
- CI run records
- run_url-linked evidence

### 4. Identity Trust
Evidence that results are bound to identifiable signers:
- signatures
- public keys
- multi-signer configuration

## Important Limitation

This score is not “absolute security”.

It is a reproducible, evidence-based trust index.

If one component is missing or weak, the final score drops multiplicatively.
