# Fail Evidence Persistence

## Purpose

Stage228 adds forensic evidence persistence to the Stage227 fail-detection pipeline.

The flow is:

Attack
↓
Fail detection
↓
Log persistence
↓
SHA256 hashing
↓
Evidence fixation

## Why this matters

Stage227 shows that the system can detect a failure.

Stage228 shows that the failure can be preserved as tamper-evident evidence.

This is important for:

- forensic analysis
- auditability
- external review
- claim-to-evidence traceability

## Output

Generated artifacts:

- `out/failures/*.log`
- `out/fail_evidence/*.evidence.json`
- `out/fail_evidence/index.json`

## Verification

You can verify whether the stored fail evidence still matches the original log by running:

```bash
python3 tools/verify_fail_evidence.py --index out/fail_evidence/index.json

If a log is modified after evidence creation, verification fails.
