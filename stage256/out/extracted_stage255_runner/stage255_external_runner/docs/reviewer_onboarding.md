# Stage243: External Reviewer Onboarding Framework

MIT License © 2025 Motohiro Suzuki

## Purpose

Stage243 prepares the repository for real independent external reviewers.

This stage does not claim that a real external reviewer is already active.
Instead, it provides the structure required to onboard one safely and transparently.

## Goals

- define how external reviewers are registered
- define what metadata is stored
- define how reviewer public keys are added
- ensure verification fails safely when no active external reviewer exists
- allow activation later without redesigning the system

## Reviewer Principles

An external reviewer must:

- be independent from the owner-controlled signer set
- control their own private key
- provide only the public key to the repository
- review according to an agreed scope

The repository must never store the reviewer's private key.

## Activation Model

Before activation:

- reviewer registry may be empty
- verification requiring an active reviewer must fail

After activation:

- reviewer metadata is added
- reviewer public key is added
- reviewer state becomes active
- reviewer signature can satisfy the external requirement

## Minimum Reviewer Metadata

- reviewer_id
- display_name
- contact
- key_path
- key_fingerprint
- status
- scope
- added_at

## Security Meaning

Stage243 is a preparation stage for real independent review.

It upgrades the project from:

- external reviewer role exists in policy

to:

- external reviewer onboarding is operationally defined

## Future Activation

A future stage can activate a real reviewer by:

1. generating a keypair on the reviewer's own device
2. sharing only the public key
3. registering reviewer metadata
4. collecting an external signature
5. verifying approval under the same policy framework
