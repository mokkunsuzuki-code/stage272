# External Timestamp Anchoring

## Purpose

This stage binds the latest transparency checkpoint state to an externally observable
GitHub Actions execution record.

The goal is not to claim an RFC3161 TSA or blockchain anchor.
Instead, the goal is to produce a reproducible and honest external timestamp anchor
based on public CI execution metadata.

## Flow

1. Generate `out/anchors/anchor_request.json`
2. Bind the latest transparency checkpoint state into that request
3. Run GitHub Actions
4. Generate `out/anchors/github_anchor_receipt.json`
5. Verify that:
   - the receipt points to the exact request hash
   - the checkpoint identity matches
   - the run URL is present

## Security Meaning

This stage strengthens evidence in the following sense:

- checkpoint state exists
- anchor request hashes that exact state
- receipt ties the request hash to an externally observable CI run
- third parties can later verify request ↔ receipt consistency

## Limits

This is not a formal trusted timestamp authority.
This is an external public-platform anchor using GitHub Actions metadata.

## Main Files

- `tools/generate_anchor_request.py`
- `tools/record_github_anchor.py`
- `tools/verify_external_anchor.py`
- `out/anchors/anchor_request.json`
- `out/anchors/github_anchor_receipt.json`
