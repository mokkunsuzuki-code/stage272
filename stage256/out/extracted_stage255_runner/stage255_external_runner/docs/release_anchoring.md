# Release Anchoring

## Purpose

Stage250 binds Stage249 anchor artifacts into a release-oriented public anchoring unit.

This stage does not claim immutable global timestamping or blockchain finality.
Instead, it produces a reproducible release manifest and binds that manifest to a
public GitHub Actions execution receipt.

## Flow

1. Use Stage249 anchor outputs as input
2. Generate `out/release_anchor/release_manifest.json`
3. Record public GitHub Actions execution metadata
4. Generate `github_release_anchor_receipt.json`
5. Verify manifest ↔ receipt consistency

## Security Meaning

This stage strengthens evidence by moving from CI-only anchoring to a
release-oriented anchoring structure.

It proves:

- Stage249 anchor artifacts existed
- they were bound into a release manifest
- that manifest was tied to a public CI execution
- the relationship is reproducible and verifiable

## Limits

This is not an RFC3161 timestamp authority.
This is not a blockchain anchor.
This is a public release-oriented anchor using GitHub Actions metadata.

## Main Files

- `tools/generate_release_manifest.py`
- `tools/record_release_anchor_receipt.py`
- `tools/verify_release_anchor.py`
- `out/release_anchor/release_manifest.json`
- `out/release_anchor/github_release_anchor_receipt.json`
