# Issue #492 -- offline verification

**Command:**

```
python -m pytest -m "not requires_live_project" -q
python -m pytest tests/operations/test_issue492_possibility_resolver_cast_offline.py -q
```

**Result:** PASS (cron run 2026-09-25)
