# Issue #678 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #678 (P2) -- AnnotationDefOperations Delete HVO membership  
**Parent triage:** #676 CheckOperations DeleteCheckType HVO family; #666 AnnotationDef Duplicate HVO (open PR)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#678** filed this run (AnnotationDef Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the definition in the owner's `PossibilitiesOS` by comparing
   each member's `Hvo` to `anno_def.Hvo`, not `anno_def in PossibilitiesOS`.
2. If not found and the owner exposes `SubPossibilitiesOS`, scan that sequence by
   `Hvo` the same way.
3. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #676 DeleteCheckType).
4. Tag the lookup with `issue #678` in comments.
5. Do not refactor unrelated AnnotationDefOperations paths in this PR.

**Out of scope:** Note Delete ResponsesOS `in` checks, possibility_item_base Delete,
Duplicate `IndexOf` sites already covered by open PRs (#642-#677).

## Verification plan

- Offline: `tests/operations/test_issue678_annotationdef_delete_hvo_offline.py`
- Live: `tests/operations/test_issue678_annotationdef_delete_hvo_live.py`
- Evidence: `specs/678-annotationdef-delete-hvo/evidence/`
