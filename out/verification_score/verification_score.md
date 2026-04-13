# Stage269 Verification Score

Stage269 reuses the deterministic trust score from Stage268.

**Total Trust:** `0.125`

## Component Scores

- **Time Trust:** `0.25`  (bitcoin-evidence-found-but-confirmations-not-parsed)
- **Integrity Trust:** `1.0`  (sha256:yes, ots:yes)
- **Execution Trust:** `0.5`  (workflows:yes, ci_evidence:no)
- **Identity Trust:** `1.0`  (signatures:yes, public_keys:yes, multi_signer:yes)

## Formula

`Total Trust = Time × Integrity × Execution × Identity`

## Important Meaning

- This is a reproducible trust index.
- This score is later used by the Stage269 gate.
- Time settlement may remain pending even when other dimensions are strong.

