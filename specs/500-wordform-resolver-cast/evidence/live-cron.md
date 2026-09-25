# Issue #500 -- live verification (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue500_wordform_resolver_cast_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx init failed: `No module named 'clr'`)

**Result:** FAIL: unverified -- cloud agent has no FieldWorks / pythonnet CLR.

**Offline gate:**

```
python3 -m pytest tests/operations/test_issue500_wordform_resolver_cast_offline.py -q
```

2 passed.
