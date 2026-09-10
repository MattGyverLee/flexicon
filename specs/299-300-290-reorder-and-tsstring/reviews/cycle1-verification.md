# Verification Report -- issue #290 pre-fix live reflection (cycle 1)

**Verdict:** [PASS] (reflection-only cycle -- no fix exists yet to
verify; this report confirms the required pre-fix evidence now exists)
**Live run:** yes | **run_mode:** live
**Evidence:** specs/299-300-290-reorder-and-tsstring/evidence/live-290-reflection.md
(raw JSON: specs/299-300-290-reorder-and-tsstring/evidence/live-290-reflection-raw.json)
**Project:** Target | **Fixture:** target_sandbox

## Scope

This cycle was READ-ONLY reflection plus isolating live calls only, per
dispatch instructions. No fix was attempted or written. New test file:
tests/operations/test_issue290_const_chart_reflection.py (3 tests, all
passed live).

## Five-question resolution table

| # | Question | Verdict |
|---|---|---|
| 1 | IConstChartRow.Label CLR type (bare ITsString claim) | CONFIRMED OK (claim correct: `SIL.LCModel.Core.Text.TsString`, no set_String/get_String) |
| 2 | IConstChartRow.Notes CLR type (was UNDETERMINED, sites :137/:414) | CONFIRMED BROKEN (isolating hit `Create(chart, notes=..., label=None)` raised `AttributeError` at line 137, independent of the Label crash) |
| 3 | GetLabel (:299) / GetNotes (:375) `.get_String(ws)` | CONFIRMED BROKEN (both raise `AttributeError` live) |
| 4 | DiscourseOperations.py:888/950 `hasattr(cell,"Label")` reachability | DEAD BRANCH (confirmed live: none of the four concrete cell-part types -- ConstChartWordGroup, ConstChartTag, ConstChartClauseMarker, ConstChartMovedTextMarker -- exposes Label; real `GetCells(row)` -> `SetCellContent`/`GetCellContent` on the two reachable types fell through to `FP_ParameterError`) |
| 5 | DiscourseOperations.py:892 Comment branch, genuine IMultiString? | BLOCKED on that specific claim (none of the four types has Comment either, so this run cannot confirm/refute genuineness for whatever other type the branch may target; left untouched as instructed) |

## Bonus findings (out of #290 scope, not fixed, flagged for separate
tracking)

- `ConstChartClauseMarkerOperations.Create` never attaches the new
  marker to `row.CellsOS` (checks `hasattr(row, "ClauseMarkersOS")`,
  which is false on a real row) -- the marker becomes unreachable via
  `GetCells`.
- `ConstChartMovedTextOperations.Create` raises a live
  `System.NullReferenceException` in `ConstChartMovedTextMarker.
  set_Preposed`, reproduced in isolation. This blocked (and was worked
  around for) the Q4 reflection on that one type.

## Mock suite (regression, supplementary)

Not run this cycle -- reflection-only scope, no code changed.

## Blockers

None. All five questions resolved from live evidence.

## Recommendation

APPROVE the reflection evidence as complete and sufficient to unblock
the #290 fix. The fix itself (routing Label/Notes through the
`_MakeTsString`/`_ReadTsString` house idiom on `ConstChartRowOperations`,
and leaving `DiscourseOperations.py:888-892` untouched per the confirmed
dead-branch findings) is separate follow-up work, not part of this
cycle.
