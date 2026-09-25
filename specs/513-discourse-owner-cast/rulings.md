# Issue #513 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #513 (P2) -- DiscourseOperations raw `.Owner` on delete/duplicate paths  
**Parent triage:** Owner-cast pattern (#97/#116); chart/row resolvers fixed in #510

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (all prior issues closed)
- **Filed and selected #513** this run: `DeleteChart`, `DeleteRow`, and `Duplicate`
  in `TextsWords/DiscourseOperations.py` use bare `obj.Owner` + `hasattr` for
  `ChartsOC` / `RowsOS` instead of `_GetTypedOwner()`.

## RULING (binding)

1. **DeleteChart** -- replace `owner = chart_obj.Owner` with
   `owner = self._GetTypedOwner(chart_obj)` before `ChartsOC.Remove`.
2. **DeleteRow** -- replace `owner = row_obj.Owner` with
   `owner = self._GetTypedOwner(row_obj)` before `RowsOS.Remove`.
3. **Duplicate** -- replace `parent = source.Owner` with
   `parent = self._GetTypedOwner(source)` before `ChartsOC.Add`.
4. Keep the ownership capability checks outside the transaction (existing shape).
5. Raise `FP_ParameterError` when `_GetTypedOwner` returns None or the typed owner
   lacks the expected collection (same messages as today).

**Out of scope:** `GetOwningText` owner-chain navigation (#513 follow-up if needed);
`ConstChart*` module methods (already aligned).

## Verification plan

- Offline: `tests/operations/test_issue513_discourse_owner_cast_offline.py`
- Live: `tests/operations/test_issue513_discourse_owner_cast_live.py`
  (`target_sandbox`; create `TEST_513_` chart/row, delete via HVO, assert counts)
- Evidence: `specs/513-discourse-owner-cast/evidence/offline-513-cron.md`
