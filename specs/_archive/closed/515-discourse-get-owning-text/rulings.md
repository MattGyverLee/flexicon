# Issue #515 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #515 (P2) -- `DiscourseOperations.GetOwningText` raw `.Owner` chain  
**Parent triage:** Owner-cast / #275 resolver family; #513 scoped Delete/Duplicate only

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#513 has open PR #514)
- **Filed and selected #515** this run: `GetOwningText` still walks bare
  `chart_obj.Owner` / `owner.Owner` and calls `IText(text_owner)` directly

## RULING (binding)

1. After `__GetChartObject`, set `st_text = self._GetTypedOwner(chart_obj)`.
2. If `st_text` is None or `st_text.Owner` is None, raise
   `FP_ParameterError("Chart has no valid owning text")`.
3. Return `self.__GetTextObject(st_text.Owner)` so the text HVO/pass-through
   path uses the #508 ClassName cast (Defect 1 from #275).
4. Do not widen to `GetAllCharts` / `ContentsOA.ChartsOC` (separate LCM path
   debt documented in tier1 queue).

## Verification plan

- Offline: `tests/operations/test_issue515_get_owning_text_offline.py`
- Live: `tests/operations/test_issue515_get_owning_text_live.py`
  (read-only Sena 3 or Target; chart HVO + pass-through chart object)
- Evidence: `specs/515-discourse-get-owning-text/evidence/`
