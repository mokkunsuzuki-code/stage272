# Signed Evidence Bundle

Stage230 introduces a signed evidence bundle.

## Goal

Move from individual proof points to a surface-level proof structure:

- fail evidence
- transparency artifacts
- checkpoint artifacts
- proof artifacts
- security documentation

These are collected into one deterministic manifest and signed.

## Outputs

- `out/bundle/evidence_bundle_payload.json`
- `out/bundle/evidence_bundle_signature.json`
- `out/bundle/evidence_bundle_summary.json`

## Verification Meaning

A reviewer can verify:

1. the manifest itself was not modified,
2. the manifest was signed by the expected key,
3. every referenced file still matches its recorded SHA256.

This changes the project from:

- "there are several pieces of evidence"

to:

- "there is one signed surface that binds those evidence pieces together".
