# Issue #680 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #680 (P2) -- NoteOperations Delete HVO membership  
**Parent triage:** #678 AnnotationDefOperations Delete HVO family; #658 Note Duplicate HVO (open PR)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#680** filed this run (Note Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the note in the owner's `AnnotationsOC` by comparing each
   member's `Hvo` to `note.Hvo`, not `note in AnnotationsOC`.
2. If not found and the owner exposes `ResponsesOS`, scan that collection by `Hvo`
   the same way.
3. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #678 AnnotationDef Delete).
4. Tag the lookup with `issue #680` in comments.
5. Do not refactor unrelated NoteOperations paths in this PR.

**Out of scope:** Duplicate `IndexOf` (#658 open PR), scripture reply attach
`IndexOf`, AnnotationDef/Check Delete paths covered by open PRs (#676, #678).

## Verification plan

- Offline: `tests/operations/test_issue680_note_delete_hvo_offline.py`
- Live: `tests/operations/test_issue680_note_delete_hvo_live.py`
- Evidence: `specs/680-note-delete-hvo/evidence/`
