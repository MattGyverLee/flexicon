# Issue #483 -- offline verification

**Command:**

```
python -m pytest tests/operations/test_issue483_naturalclass_phoneme_resolver_cast_offline.py -m "not requires_live_project" -q
```

**Result:** PASS 2/2

**run_mode:** mock (cloud pod; no FieldWorks)

**Live:** FAIL: unverified (no live LCM in this environment)
