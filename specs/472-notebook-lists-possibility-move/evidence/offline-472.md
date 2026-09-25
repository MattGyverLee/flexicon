# Issue #472 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue472_possibility_reparent_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent session; no FLEx init)

**Result:** PASS (see pytest output in CI / cron log)

**Live LCM:** FAIL: unverified (FieldWorks / Target not available in cloud cron pod)
