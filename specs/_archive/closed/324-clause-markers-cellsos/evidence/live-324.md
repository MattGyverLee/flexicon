# Issue #324 -- live LCM verification

**Command (required):**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue324_clause_markers_cellsos.py -m requires_live_project -q
```

**Environment:** Cloud agent Linux pod -- no FieldWorks, no Target `.fwbackup`
fixture, no `SIL.LCModel`.

**run_mode:** not executed (no `tests/live_status.json` update on this host)

**Result:** FAIL: unverified -- live LCM verification must be run on a
FieldWorks Windows machine before merge. The live test
`TestIssue324ClauseMarkersCellsOSLive.test_create_persists_in_cellsos_and_getall`
asserts post-state marker HVO in `row.CellsOS` and round-trip via `GetAll` /
`Find` after `Delete`.

**Pre-state (expected):** empty `row.CellsOS` after `ConstChartRows.Create`.

**Post-state (expected):** created marker HVO present in `row.CellsOS`;
`GetAll(row)` length 1; removed after `Delete`.
