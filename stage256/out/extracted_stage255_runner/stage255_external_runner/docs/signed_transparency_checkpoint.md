# Signed Transparency Checkpoint

## Overview

Stage218 introduces a signed checkpoint over the transparency log state.

The model is:

Merkle Root
↓
Signature
↓
Checkpoint

This allows the transparency log state to be fixed and independently verified at a specific point in time.

## Security Purpose

A Merkle tree alone provides commitment to the log contents.

A signed checkpoint adds:

- authenticated log state
- explicit tree size
- explicit root hash
- replayable verification point
- auditable checkpoint history foundation

## Files

- `out/transparency/transparency_log.json`
- `out/transparency/merkle_tree.json`
- `out/checkpoint/checkpoint_payload.json`
- `out/checkpoint/checkpoint.json`

## Verification

The checkpoint can be verified by:

1. reconstructing the canonical payload
2. decoding the signature
3. verifying the Ed25519 signature using the embedded public key

## Positioning

This is a Certificate Transparency-inspired structure for evidence transparency,
but adapted to the QSP research transparency workflow rather than public web PKI.
