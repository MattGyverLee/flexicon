# Issue #552 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #552 (P2) -- ExampleOperations Duplicate insert_after ExamplesOS index  
**Parent triage:** #550 LexSense Duplicate; #548 Environment; #531 Paragraph HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#552** filed this run (ExampleOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source example in
   `parent.ExamplesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `ExamplesOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #552` in comments.
4. Do not refactor unrelated ExampleOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue552_example_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue552_example_duplicate_hvo_live.py`
- Evidence: `specs/552-example-duplicate-hvo/evidence/`
