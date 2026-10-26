# Issue #772 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #772 (P2) -- OverlayOperations Delete HVO membership  
**Parent triage:** #736 OverlayOperations PossItemsRC Add/RemoveElement HVO (open PR)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#772** filed this run (Overlay Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the overlay in `ILangProject.OverlaysOC` by comparing each
   member's `Hvo` to the resolved overlay's `Hvo`, not `overlay in OverlaysOC`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #680 Note Delete and #736 RemoveElement).
3. Tag the lookup with `issue #772` in comments.
4. Do not refactor unrelated OverlayOperations paths in this PR.

**Out of scope:** PossItemsRC Add/RemoveElement (#736 open PR), Duplicate insert_after,
chart association helpers.

## Verification plan

- Offline: `tests/operations/test_issue772_overlay_delete_hvo_offline.py`
- Live: `tests/operations/test_issue772_overlay_delete_hvo_live.py`
- Evidence: `specs/772-overlay-delete-hvo/evidence/`
