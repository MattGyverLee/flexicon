# Issue #510 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #510 (P2) -- DiscourseOperations chart/row pass-through #275 gap  
**Parent triage:** #275 resolver family; ConstChart* modules already aligned

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (all prior P2 issues closed with merged PRs)
- Open **P3** bugs without an open PR: **none**
- **Filed and selected #510** this run: `__GetChartObject` / `__GetRowObject` in
  `TextsWords/DiscourseOperations.py` omit ClassName cast on the pass-through path
  when callers supply `project.Object(hvo)`

## RULING (binding)

1. Add `__CastChartView` mirroring `ConstChartOperations.__ResolveObject` ClassName
   dispatch (`DsConstChart` -> `IDsConstChart`, `DsChart` -> `IDsChart`) with the
   existing try/fallback cast sequence for already-typed inputs.
2. Route both HVO and pass-through chart arguments through ClassName dispatch before
   return; reject unknown HVO ClassNames with `FP_ParameterError`.
3. Align `__GetRowObject` with `ConstChartRowOperations.__ResolveObject` (ClassName
   `ConstChartRow` -> `IConstChartRow` on int and pass-through).

Out of scope: `ConstChartOperations` module resolvers (already fixed), chart factory
defects in `CreateChart` (Q-DISC1).

## Verification plan

- Offline: `tests/operations/test_issue510_discourse_chart_row_resolver_offline.py`
- Live: `tests/operations/test_issue510_discourse_chart_row_resolver_live.py`
  (`target_sandbox`; chart HVO + raw `Object(hvo)` on `GetChartName` / row paths)
