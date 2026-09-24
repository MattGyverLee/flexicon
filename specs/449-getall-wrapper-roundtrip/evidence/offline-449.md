# Issue #449 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue449_wrapper_unwrap_offline.py -m "not requires_live_project" -q
```

**Environment:** Cloud agent (no libmono / FieldWorks).

**Result:** PASS (3/3) -- source ratchet only; flexicon import unavailable without mono.

**Live:** FAIL: unverified (no FieldWorks on cloud agent).
