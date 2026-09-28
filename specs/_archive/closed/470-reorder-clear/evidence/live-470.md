# Issue #470 -- live verification evidence

**Command:**

```bash
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue470_reorder_clear_live.py -m requires_live_project -q
```

**run_mode:** mock (no FieldWorks / pythonnet in cloud pod)

**Result:** FAIL: unverified

**Notes:** Gate file not added in this PR; live repro requires Target/Sena3
sandbox per issue checklist.
