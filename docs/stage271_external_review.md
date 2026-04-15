# Stage271: External Review Linked Proof

## Purpose

Stage271 turns external review itself into a verifiable object.

Instead of:

- "someone reviewed it"

Stage271 makes it possible to verify:

- who reviewed
- what was reviewed
- what verdict/result was given
- which prior verification artifact it was linked to
- whether the review record was tampered with later

## What is linked

A review record is linked to a Stage270 verification artifact such as:

- gate_result.json
- verification_score.json

## What is added

Each review record includes:

- reviewer identity metadata
- verdict/result
- free-text comment
- target artifact path
- target artifact SHA256
- previous review SHA256

This creates a review chain.

## Why this matters

Normal reviews are trust-based.

Stage271 makes reviews partially verification-based.

That is the key transition from:

- "review exists"

to

- "review record is reproducible and tamper-evident"

## Limits

Stage271 does not prove that the reviewer is globally authoritative.

It proves that the review record:

- exists
- was linked to a specific target artifact
- was signed
- was chain-connected
- can be re-verified later

## Next strategic use

This stage is suited for:

- OpenSSF outreach
- external researcher review
- review history accumulation
- turning comments/reject/accept decisions into auditable evidence
