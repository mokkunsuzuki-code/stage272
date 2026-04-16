# Stage239 Verification Policy Enforcement

This stage moves from merely generating attestations to enforcing them as an
acceptance policy.

## Goal

A build is accepted only if:

1. a build provenance attestation exists,
2. an SBOM attestation exists,
3. both attestations verify successfully,
4. the signer workflow matches the expected reusable workflow,
5. the artifact identity matches the expected subject,
6. the SBOM predicate type is SPDX 2.3.

If any of these checks fail, the workflow fails.

## Security Meaning

This stage upgrades the project from:

- "we produced attestations"

to:

- "we reject builds that do not satisfy the attestation policy"

That is closer to governance / admission control rather than simple evidence generation.
