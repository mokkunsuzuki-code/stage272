# Stage273: Structured Review Context

## Purpose

Stage273 extends Stage272 by structuring review context.

A review record should not only say that a review happened.
It should also say what artifacts were reviewed.

This stage adds:

- SBOM linkage
- vulnerability scan linkage
- reproducible hash binding to those artifacts

## Why this matters

Without structured review context, a review record may exist,
but the precise review target remains ambiguous.

Stage273 reduces that ambiguity by explicitly binding the review to:

- a specific SBOM file
- a specific vulnerability scan result

## What this stage proves

Stage273 proves that a review record can be linked not only to
a verification artifact, but also to supporting supply-chain artifacts.

## What this stage does not prove

This stage does not prove that the SBOM is complete
or that the vulnerability scan is perfect.

It proves only that the review record is explicitly linked to those artifacts.

