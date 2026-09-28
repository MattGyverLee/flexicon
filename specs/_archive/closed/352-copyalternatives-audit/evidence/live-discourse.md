# Live evidence -- #352 Discourse face (cell Label/Comment)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_discourse_live.py -m requires_live_project -q
```

## Classification (snapshot)

- No `Label`/`Comment` on any chart-cell type (`IConstChartWordGroup`,
  `IConstChartTag`, `IConstChartClauseMarker`,
  `IConstChartMovedTextMarker`); only `IConstChartRow.Label`/`Notes`
  exist, as bare `ITsString` (snapshot 7749/7714).

## Fix (`flexicon/code/TextsWords/DiscourseOperations.py`)

- `SetCellContent`: the `Label` branch now dispatches on shape --
  `set_String` when the member is a real multistring, house
  `_MakeTsString` assignment for bare-ITsString Labels (rows). The
  `Comment` branch and the honest `FP_ParameterError` else-branch are
  unchanged: genuine cell parts still raise actionably.
- `GetCellContent`: falls back to `_ReadTsString` when the
  `get_String` read fails, so row labels read back instead of the
  old permanent "".

## Post-fix values read back from the LCM

- Row created with label -> `GetCellContent` returns it;
  `SetCellContent` relabels (confirmed via `ConstChartRows.GetLabel`);
  unsupported object still raises `FP_ParameterError`.

## Pass/fail

**PASS.** `2 passed` on the command above, live run_mode.
