# External Reviewer Policy

## Purpose

This document defines how real external reviewers can participate in the QSP review process.

The goal is not to ask an external reviewer to guarantee the entire security of the project.
The goal is to provide a realistic and bounded path for third-party review.

---

## Reviewer Roles

### Owner
The repository maintainer who prepares the review packet, evidence, and repository state.

### Internal Reviewer
A reviewer operating within the repository workflow or project environment.

### External Reviewer
A real third party who can independently inspect selected materials, reproduce verification steps,
and leave a recorded verdict.

---

## What External Review Means

External review in this repository means that a third party may:

- inspect selected repository materials
- execute documented verification steps
- confirm whether outputs are reproducible
- leave a scoped review verdict
- optionally sign or acknowledge a review record

External review does not automatically mean:

- full security approval
- formal cryptographic proof endorsement
- operational deployment approval
- legal or organizational certification

---

## Scope Boundaries

External reviewers are not required to review the entire codebase.

They may review a bounded packet including:

- README
- claim summary
- evidence bundle
- transparency checkpoint
- review instructions
- selected verification scripts

The exact scope must be declared in the review packet.

---

## Responsibility Boundaries

External reviewers are expected to state only what they actually checked.

They should avoid making claims beyond the scope of their review.

Examples of acceptable scoped statements:

- I reproduced the documented verification command.
- I reviewed the listed evidence artifacts.
- I observed that the output structure matches the documentation.

Examples of statements outside normal scope:

- The entire protocol is secure.
- This repository is production-safe in all settings.
- All cryptographic assumptions are proven.

---

## Output of Review

Each external review should produce a review record containing:

- reviewer identifier
- date
- repository name
- reviewed commit
- reviewed artifacts
- verdict level
- comments
- optional acknowledgment or signature reference

---

## Philosophy

This stage is designed to move from:

reviewer role exists

to

a real third party can participate in a bounded and recorded way

This is an activation step for research credibility, real-world readiness, and external evaluation.
