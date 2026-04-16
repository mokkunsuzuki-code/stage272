# Review Verdict Levels

This document defines the meaning of each review verdict used in Stage244.

---

## observed

The reviewer inspected the materials but did not reproduce the steps.

Example:
- Read the documentation
- Inspected the packet structure
- Confirmed that the declared review scope is clear

---

## reproduced

The reviewer executed documented commands and reproduced expected outputs.

Example:
- Ran the review packet generator
- Verified that the example review record passes validation

---

## reviewed

The reviewer inspected the declared artifacts and is comfortable stating that the bounded review was completed.

Example:
- Reviewed the packet
- Reproduced the verification steps
- Confirmed that the record structure is coherent

---

## approved

A stronger statement than reviewed.

This should only be used when the reviewer intentionally wants to express positive approval within the declared scope.

This does not automatically mean approval of the whole repository or all security claims.

---

## Important Principle

Verdicts apply only to the declared review scope.

No verdict should be interpreted beyond the explicit scope of review.
