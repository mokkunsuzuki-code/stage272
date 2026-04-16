# Stage256 External Execution Record

## Goal

Stage256 records independently executed QSP runs performed by external reviewers.

Each execution produces a receipt containing:

- reviewer_id
- executed_at_utc
- bundle_manifest_sha256
- anchor_sha256
- qsp_result_sha256
- command_used

The review log aggregates all recorded receipts.

## Main files

- `tools/record_external_execution.py`
- `tools/verify_external_execution_record.py`
- `tools/run_stage256_external_record.sh`

## Outputs

- `out/external_execution_record/review_log.json`
- `out/external_execution_record/review_log.json.sha256`
- `out/external_execution_record/receipts/*.json`

## Meaning

This stage upgrades external execution from:

- "a third party can run QSP"

to:

- "a third party run is recorded and later verifiable"

This makes reviewer activity auditable and reproducible.
