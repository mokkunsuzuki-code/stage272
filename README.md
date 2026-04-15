# QSP / Stage271
# External Review Linked Proof

Stage271 records external review outcomes as **verifiable evidence** linked to a prior verified target artifact.

This stage extends Stage270 by adding:

- external review record generation
- cryptographic hash linkage
- signature over each review record
- review-chain verification
- CI artifact generation for public re-checking

The goal is to turn review itself into an auditable object.

---

## Why Stage271 matters

Stage270 proves that the internal verification gate reached an `accept` decision with settled time trust.

Stage271 adds a new layer:

- internal proof -> external review proof

Instead of only saying:

- "an external party reviewed this"

Stage271 makes it possible to verify:

- which artifact was reviewed
- which reviewer identity metadata was attached
- what result/comment was recorded
- what previous review record it links to
- whether the review record was tampered with later

This moves the project from:

- **internally proven**
to
- **externally reviewable and review-record-verifiable**

---

## Core Concept

Each review record contains:

- reviewer metadata
- result (`accept` / `pending` / `reject` / `comment`)
- free-text review comment
- linked Stage270 verification artifact path
- SHA256 of that target artifact
- previous review SHA256

This creates a tamper-evident review chain.

---

## Repository Structure

- `schemas/external_review_record.schema.json`  
  JSON schema for review records

- `external_reviewers/reviewer_registry.json`  
  Reviewer registry / metadata

- `review_records/*.json`  
  Individual review records

- `tools/create_stage271_review_record.py`  
  Creates a review record linked to Stage270 evidence

- `tools/sign_stage271_review.py`  
  Signs a review record with Ed25519

- `tools/verify_stage271_review_chain.py`  
  Verifies signatures, hashes, and chain order

- `tools/build_stage271_summary.py`  
  Builds a human-readable summary

- `docs/stage271_external_review.md`  
  Explanation and scope

- `.github/workflows/stage271-external-review-linked.yml`  
  CI workflow

---

## What This Stage Proves

Stage271 proves that review records can be:

- linked to a specific verification artifact
- hashed deterministically
- signed
- chained to prior review records
- re-verified later by anyone with the public key and repository contents

This does **not** prove that the reviewer is globally authoritative.

It proves that the review record itself is:

- present
- linked
- signed
- chain-consistent
- tamper-evident

---

## Quick Start

### 1. Create a review record

```bash
python tools/create_stage271_review_record.py \
  --reviewer-id self-demo-reviewer \
  --result comment \
  --comment "Bootstrap review linked to Stage270 verification artifact."
2. Sign it
latest_review=$(ls review_records/*.json | sort | tail -n 1)
python tools/sign_stage271_review.py --review "$latest_review"
3. Verify the review chain
python tools/verify_stage271_review_chain.py
4. Build summary
python tools/build_stage271_summary.py
Example Review Record
{
  "version": "1",
  "review_id": "example1234abcd",
  "stage": "stage271",
  "target_artifact": "out/vep/gate_result.json",
  "reviewer": {
    "id": "self-demo-reviewer",
    "type": "local_external_placeholder",
    "display_name": "External Reviewer Placeholder",
    "contact": "pending"
  },
  "review_result": "comment",
  "review_comment": "Bootstrap review linked to Stage270 verification artifact.",
  "timestamp_utc": "2026-04-15T00:00:00Z",
  "linked_verification": {
    "path": "out/vep/gate_result.json",
    "sha256": "..."
  },
  "previous_review_sha256": "GENESIS"
}
Strategic Value

Stage271 is the bridge between:

evidence generation
external evaluation
standards-adjacent reviewability

This is especially useful before outreach to organizations such as OpenSSF because it shows that the project treats review itself as a verifiable supply-chain-style artifact.

That is the key difference between:

“please trust this review”
and
“please verify this review record”
Limits and Accuracy

This stage does not claim:

formal academic peer review
standards approval
universal reviewer trust
security proof of reviewer honesty

This stage only claims deterministic, signed, chain-verifiable review recording.

License

MIT License

Copyright (c) 2025 Motohiro Suzuki

