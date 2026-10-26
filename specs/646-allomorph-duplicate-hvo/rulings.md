# Issue #646 -- lex-lead ruling

**Date:** 2026-10-22  
**Issue:** #646 (P2) -- AllomorphOperations Duplicate insert_after AlternateFormsOS index  
**Parent triage:** #644 PronunciationOperations; #597 VariantOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#646** filed this run (AllomorphOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True` and the source is an alternate form,
   locate the source in `parent.AlternateFormsOS` by comparing each member's
   `Hvo` to `source.Hvo`, not `AlternateFormsOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #646` in comments.
4. Do not refactor unrelated AllomorphOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes; lexeme-form branch.

## Verification plan

- Offline: `tests/operations/test_issue646_allomorph_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue646_allomorph_duplicate_hvo_live.py`
- Evidence: `specs/646-allomorph-duplicate-hvo/evidence/`
