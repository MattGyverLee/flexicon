# Cycle 2 -- Programmer report: issue #270 Tier 4 executability fix

## File changed

`tests/operations/test_collection_cast_pattern.py` (only file touched; no
production file changed -- confirmed via `git diff --stat`, which shows a
single file modified).

## Corrected diagnosis

Accessor typo, not missing Sena 3 data. `FLExProject` exposes the property
`ConstCharts` (`flexicon/code/FLExProject.py:2820`); there is no
`ConstChart` accessor and the class defines no `__getattr__`, so
`sena3_sandbox.ConstChart.GetAll()` raised `AttributeError` before the
`pytest.skip(...)` on the empty-charts branch could ever execute. The test
never reached its Tier 4 assertion regardless of what Sena 3 contained.

## Replacement test

`TestCollectionCastLive.test_chart_cell_tag_getall_is_not_empty_when_tags_exist`,
lines 993-1052. Marker changed to
`@pytest.mark.live_phase("ConstChartCellTagOperations", "add")` (the file's
`_LIVE_PHASES` enum in `tests/conftest.py` is `read|add|reorder|modify|delete`
-- no `create` -- and `add` matches the sibling live "construct your own
precondition" test at line 908).

Now uses `target_sandbox` (write-enabled tempdir copy of the Target
`.fwbackup`) and constructs its own precondition instead of depending on
Sena 3 content:

```python
col    = target_sandbox.ConstChartMarkers.Create("TEST_270_col")
marker = target_sandbox.ConstChartMarkers.Create("TEST_270_tag")
chart  = target_sandbox.ConstCharts.Create("TEST_270_chart")
row    = target_sandbox.ConstChartRows.Create(chart, label="TEST_270_row")
# pre-state: row.CellsOS.Count == 0
tag1   = target_sandbox.ConstChartCellTags.Create(row, col, marker)
tag2   = target_sandbox.ConstChartCellTags.Create(row, col, marker)
```

Post-state assertion re-queries the LCM (not the values passed in):
`expected = [c.Hvo for c in row.CellsOS if c.ClassName == "ConstChartTag"]`
vs. `actual = [t.Hvo for t in target_sandbox.ConstChartCellTags.GetAll(row)]`,
asserting `len(actual) == 2 and actual == expected`. Cleanup in `finally`
deletes the chart (cascades to its rows/cells per
`ConstChartOperations.Delete`'s documented cascade) and then the two
project-wide marker vocabulary items via `ConstChartMarkers.Delete`, since
those are owned by `ChartMarkersOA`, not the chart.

`python -m pytest tests/operations/test_collection_cast_pattern.py
--collect-only -q` collects all 72 tests (including the new one) with no
import/collection errors.

Out-of-scope items (ConstChartWordGroup / MovedTextMarker / ClauseMarker
mixed-type cells) were not attempted, per instructions.
