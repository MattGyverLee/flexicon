# Live verification -- issue #878

**Command:**

```text
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue878_infltype_gloss_sync_live.py -m requires_live_project -q
```

**run_mode:** mock (no FieldWorks / pythonnet CLR on cloud VM)

**Pre-state:** N/A (live run not executed)

**Post-state read back from LCM:** N/A

**Result:** FAIL: unverified
