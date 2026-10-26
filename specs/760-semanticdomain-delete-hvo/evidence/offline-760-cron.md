# Issue #760 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue760_semanticdomain_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (cloud agent)

**Result:** PASS (see pytest output in PR / CI)
