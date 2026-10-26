# Issue #804 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue804_lexsense_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud agent -- no FieldWorks / pythonnet LCM)

**Pre-state / post-state from LCM:** not collected (live gate blocked)

**Result:** FAIL: unverified -- run on Target sandbox on a FieldWorks host before merge.
