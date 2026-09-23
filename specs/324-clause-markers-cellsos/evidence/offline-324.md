# Issue #324 -- offline verification

**Command attempted:**
```
python3 -m pytest tests/operations/test_issue324_clause_markers_cellsos.py -m "not requires_live_project" -q
```

**Environment:** Cloud agent Linux pod (no libmono / no FieldWorks).

**Result:** FAIL: unverified -- collection aborts importing `flexicon` because
pythonnet cannot create a .NET runtime on this host. The three mock tests in
`test_issue324_clause_markers_cellsos.py` are written for CI/Windows dev
machines with FieldWorks installed.

**Expected on Windows CI/dev:**
- `Create` adds to `row.CellsOS` and never touches `ClauseMarkersOS`
- `GetAll` / `Find` filter `ConstChartClauseMarker` cells only
