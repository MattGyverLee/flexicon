# Issue #658 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #658 (P2) -- NoteOperations Duplicate / AttachReply insert_after ResponsesOS index  
**Parent triage:** #597 VariantOperations; #652 LocationOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#658** filed this run (NoteOperations sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `__AttachReply` when `insert_after=True`, locate `after_source` in
   `scr_parent.ResponsesOS` by comparing each member's `Hvo` to
   `after_source.Hvo`, not `ResponsesOS.IndexOf(after_source)`.
2. In `Duplicate` when `insert_after=True` on the `ResponsesOS` owner branch,
   locate `source` by `Hvo` the same way.
3. If no member matches, append at `len(sequence)` (do not insert at index 0
   when lookup fails).
4. Tag both lookups with `issue #658` in comments.
5. Do not refactor unrelated NoteOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites (AnnotationDef, Anthropology,
PossibilityList, …).

## Verification plan

- Offline: `tests/operations/test_issue658_note_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue658_note_duplicate_hvo_live.py`
- Evidence: `specs/658-note-duplicate-hvo/evidence/`
