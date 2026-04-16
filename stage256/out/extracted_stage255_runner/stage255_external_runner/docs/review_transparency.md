# Review Transparency

## Purpose

Stage247 introduces a tamper-evident review history for QSP.

The goal is not only to show that a review exists, but also to make the
entire review history auditable.

## What is added

- Structured review records in `review_records/*.json`
- Aggregated review log in `out/review_log/review_log.json`
- SHA-256 digest in `out/review_log/review_log_hash.txt`
- Ed25519 signature in `out/review_log/review_log.sig`
- Verification script in `tools/verify_review_log.py`

## Security idea

Each review record is hashed individually.

Those leaf hashes are then combined into a simple Merkle-style tree to produce
a single root hash (`merkle_root`).

The complete review log is hashed and signed.

This provides:

- integrity of the full review history
- tamper detection
- independent verification
- reviewer-history transparency

## Verification

A verifier can independently check:

1. the review log hash
2. each leaf hash
3. the Merkle-style root
4. the Ed25519 signature

## Meaning

Stage245:
- a review exists

Stage247:
- the review history itself becomes auditable
