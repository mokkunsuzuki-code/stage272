# Reviewer Quickstart

This guide is for a real external reviewer.

The goal is to allow a reviewer to inspect a bounded packet and verify the process quickly.

---

## 1. Clone the repository

git clone https://github.com/mokkunsuzuki-code/stage244.git
cd stage244

## 2. Generate a review request packet

python3 tools/generate_review_request.py --reviewer-id external-demo --commit demo-commit --repo stage244

## 3. Inspect the generated packet

Expected outputs:

- out/review_packets/review_request.json
- out/review_packets/review_request.md

## 4. Review the declared scope

Read:

- docs/external_reviewer_policy.md
- docs/reviewer_scope.md
- docs/review_verdict_levels.md

## 5. Inspect the review record template

Read:

- review_records/template_review_record.json
- review_records/example_external_review.json

## 6. Verify the example review record

python3 tools/verify_review_record.py --input review_records/example_external_review.json

Expected result:

[OK] review record is valid

---

## Reviewer Guidance

A reviewer does not need to approve the entire system.

A reviewer may leave a bounded verdict such as:

- observed
- reproduced
- reviewed

Use approved only when the reviewer intentionally wants to make that stronger statement.

---

## Final Output

The reviewer can leave a review record with:

- reviewer identifier
- date
- reviewed commit
- reviewed artifacts
- verdict
- notes
