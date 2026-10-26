# Issue #762 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #762 (P2) -- POSOperations Delete / RemoveSubcategory HVO membership  
**Parent triage:** #760 lex-lead ruling out-of-scope note (POS RemoveSubcategory sibling gap)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#762** (filed this run; POS delete paths)

Untrusted open issues ignored per automation policy (#635 from rulingAnts).

## RULING (binding)

1. In `Delete`, locate the top-level `PossibilitiesOS` member whose `Hvo`
   matches the resolved POS before calling `Remove`.
2. In `RemoveSubcategory`, locate the `SubPossibilitiesOS` member whose `Hvo`
   matches the resolved subcategory before calling `Remove`.
3. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
4. Tag lookups with `issue #762` in comments.
5. Do not refactor unrelated POSOperations paths in this PR.

**Out of scope:** PersonOperations Delete PossibilitiesOS HVO (next sibling gap).

## Verification plan

- Offline: `tests/operations/test_issue762_pos_delete_hvo_offline.py`
- Live: `tests/operations/test_issue762_pos_delete_hvo_live.py`
- Evidence: `specs/762-pos-delete-hvo/evidence/`
