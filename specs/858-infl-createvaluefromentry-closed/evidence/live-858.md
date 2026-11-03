# Issue #858 live verification

**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue858_infl_createvaluefromentry_closed_live.py -m requires_live_project -q`

**run_mode:** mock (FieldWorks / pythonnet not available in cloud agent VM)

**Pre-state:** N/A (live not executed)

**Post-state:** N/A

**Result:** FAIL: unverified — no live LCM session in this environment.
