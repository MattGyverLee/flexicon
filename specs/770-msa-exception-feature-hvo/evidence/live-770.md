# Issue #770 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue770_msa_exception_feature_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified — cloud agent has no FieldWorks / pythonnet `clr` stack.

**run_mode:** mock (no live LCM in this environment)

**Pre-state / post-state:** Not measured on LCM (blocked).
