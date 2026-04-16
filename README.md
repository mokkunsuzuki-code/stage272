# QSP / Stage272
# Real External Review Integration

Stage272 extends Stage271 by integrating at least one real external review into the verifiable review chain.

Stage271 proved that review records can be represented as signed, hash-linked, reproducible artifacts.

Stage272 adds:

- externally originated review evidence
- preserved source review text
- normalized review record generation
- signed review-chain integration
- CI-based re-verification

---

## Why Stage272 matters

Stage271 proved that review records could be made tamper-evident.

Stage272 proves that a real external review event can be preserved, normalized, linked, signed, and re-verified later.

This moves the system from:

- review proof mechanism

to:

- proof that an actual external review event was integrated

---

## What is added

- `external_reviews/raw/` for source review evidence
- `external_reviews/normalized/` for normalized structured review records
- `tools/create_stage272_external_review.py`
- `tools/build_stage272_summary.py`
- `docs/stage272_real_external_review.md`
- `out/external_review_evidence/` for evidence metadata

---

## Main idea

A real external review should not remain only as a web comment, message, or informal text.

It should be:

- preserved
- hashed
- normalized
- signed
- chain-linked
- re-verifiable

---

## Quick flow

1. capture the external review text
2. save it under `external_reviews/raw/`
3. normalize it into a structured review record
4. sign the review record
5. verify the chain
6. publish CI-verifiable outputs

---

## Verification

```bash
python3 -m pip install cryptography
python3 tools/verify_stage271_review_chain.py
python3 tools/build_stage272_summary.py
License

MIT License

Copyright (c) 2025 Motohiro Suzuki
