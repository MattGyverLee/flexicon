# Issue #736 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #736 (P2) -- OverlayOperations AddElement/RemoveElement PossItemsRC HVO membership  
**Parent triage:** #734 GetSensesInDomain / #320 PossItemsRC family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#736** (filed this run; sibling gap after #734 PR #735)

## RULING (binding)

1. In `AddElement`, treat the element as already present when any `PossItemsRC`
   member shares its `Hvo`; do not use Python `in` on the reference collection.
2. In `RemoveElement`, scan `PossItemsRC` for the member whose `Hvo` matches,
   then call `Remove` with that collection member reference; if none match, no-op.
3. Tag both sites with `issue #736` in comments.
4. Do not refactor unrelated OverlayOperations paths in this PR.

**Out of scope:** Allomorph `PhoneEnvRC` / `InflectionClassesRC`; Overlay
`PossListRA` list-membership warning guard (issue #320).

## Verification plan

- Offline: `tests/operations/test_issue736_overlay_possitems_hvo_offline.py`
- Live: `tests/operations/test_issue736_overlay_possitems_hvo_live.py`
- Evidence: `specs/736-overlay-possitems-hvo/evidence/`
