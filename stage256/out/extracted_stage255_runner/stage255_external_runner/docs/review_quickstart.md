# Review Quickstart (5-minute overview)

## TL;DR (3-line summary)
This project makes security claims:
- Explicit
- Reproducible
- Verifiable

Using a deterministic pipeline:

Claim → Evidence → Merkle Proof → Verification

## What is this?
This repository demonstrates a reproducible and verifiable mapping:

Security Claim
↓
Evidence Artifact
↓
Merkle Proof
↓
Independent Verification

## What is new?
- Claims are explicitly defined
- Evidence is reproducible
- Proofs are cryptographically bound
- Verification is deterministic

## 5-minute review steps
1. Read README.md
2. Run:
   ./verify_all.sh
3. Inspect:
   claims/claims.yaml
4. Check:
   out/proofs/

## What to verify
- Claims map to evidence
- Evidence is included in Merkle tree
- Proof verification passes

## Limitations
- Not a full protocol security proof
- QKD assumptions are not proven here
- Implementation completeness not guaranteed
