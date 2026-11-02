# Live verification -- issue #852

**Command (required gate):**

```text
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue852_phon_createvalue_closed_live.py -m requires_live_project -q
```

**Environment:** Cloud agent VM (no FieldWorks / pythonnet `clr`).

**tests/live_status.json `run_mode`:** mock (FieldWorks not installed on this runner).

**Pre-state:** N/A (live project not opened).

**Post-state:** N/A.

**Result:** FAIL: unverified -- live LCM proof not performed on this runner.

**Offline gate (passed on this runner):**

```text
python3 -m pytest tests/operations/test_issue852_phon_createvalue_closed_offline.py -m "not requires_live_project" -q
```
