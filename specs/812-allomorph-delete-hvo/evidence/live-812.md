# Issue #812 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue812_allomorph_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent has no FieldWorks/pythonnet)

**Pre-state / post-state:** Not read back from LCM in this environment.

**Result:** Gate module present; run on `target_sandbox` before merge.
