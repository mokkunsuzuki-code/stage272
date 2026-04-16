# Stage242: 2-of-3 Multi-Party Approval

MIT License © 2025 Motohiro Suzuki

## What changes in Stage242

Stage241 required multiple keys, but those keys could still be controlled by the same person.

Stage242 upgrades the trust model from:

- multiple keys

to:

- multiple independent approvals

This stage introduces three signer roles:

- developer
- auditor
- external reviewer

The repository enforces the following policy:

- at least 2 valid signatures are required
- at least 1 valid signature must come from an external signer
- approvals must span at least 2 independence groups

## Why this matters

This prevents a single actor from self-approving through multiple local roles.

In other words:

- technical threshold alone is not enough
- independence of approvers must be represented in policy
- verification should fail if only owner-controlled roles approve

## Security meaning

Stage242 is not only about stronger signing.
It is about stronger governance.

The policy becomes:

Assumption → Claim → Evidence → Approval Policy → Verification

## Example

Not enough:

- developer = valid
- auditor = valid
- reviewer = missing

Result:
- threshold 2 is reached
- but no external signer is present
- verification fails

Enough:

- developer = valid
- reviewer = valid

Result:
- threshold 2 is reached
- external signer is present
- at least 2 independence groups are represented
- verification succeeds
