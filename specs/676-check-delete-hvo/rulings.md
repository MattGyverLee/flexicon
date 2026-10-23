# Issue #676 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #676 (P2) -- CheckOperations DeleteCheckType HVO membership  
**Parent triage:** #664 CheckOperations Duplicate HVO family; #523 SegmentOperations Exists

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#676** filed this run (DeleteCheckType sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `DeleteCheckType`, locate the check in `check_list.PossibilitiesOS` by
   comparing each member's `Hvo` to `check_obj.Hvo`, not `check_obj in
   PossibilitiesOS`.
2. If not found at top level, scan each parent's `SubPossibilitiesOS` by `Hvo`
   the same way.
3. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #525 segment removal).
4. Tag the lookup with `issue #676` in comments.
5. Do not refactor unrelated CheckOperations paths in this PR.

**Out of scope:** AnnotationDef Delete `in` checks, Note Delete ResponsesOS,
Duplicate `IndexOf` sites already covered by open PRs (#642-#674).

## Verification plan

- Offline: `tests/operations/test_issue676_check_delete_hvo_offline.py`
- Live: `tests/operations/test_issue676_check_delete_hvo_live.py`
- Evidence: `specs/676-check-delete-hvo/evidence/`
