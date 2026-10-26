# Issue #644 -- lex-lead ruling

**Date:** 2026-10-22  
**Issue:** #644 (P2) -- PronunciationOperations Duplicate insert_after PronunciationsOS index  
**Parent triage:** #552 ExampleOperations; #597 VariantOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#644** filed this run (PronunciationOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source pronunciation in
   `parent.PronunciationsOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `PronunciationsOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #644` in comments.
4. Do not refactor unrelated PronunciationOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue644_pronunciation_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue644_pronunciation_duplicate_hvo_live.py`
- Evidence: `specs/644-pronunciation-duplicate-hvo/evidence/`
