# Issue #650 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #650 (P2) -- DataNotebookOperations Duplicate insert_after SubRecordsOS index  
**Parent triage:** #646 AllomorphOperations; #552 ExampleOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#650** filed this run (DataNotebookOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True` and the source is a sub-record,
   locate the source in `parent_record.SubRecordsOS` by comparing each
   member's `Hvo` to `source.Hvo`, not `SubRecordsOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #650` in comments.
4. Do not refactor unrelated DataNotebookOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes; top-level RecordsOC branch.

## Verification plan

- Offline: `tests/operations/test_issue650_datanotebook_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue650_datanotebook_duplicate_hvo_live.py`
- Evidence: `specs/650-datanotebook-duplicate-hvo/evidence/`
