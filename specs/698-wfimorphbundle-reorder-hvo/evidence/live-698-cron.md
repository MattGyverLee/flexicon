# Issue #698 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue698_wfimorphbundle_reorder_hvo_live.py -m requires_live_project -q
```

**run_mode:** not live (FLEx init failed: `No module named 'clr'` on cloud agent)

**Pre/post LCM readback:** not performed

**Result:** FAIL: unverified (blocker: no FieldWorks/pythonnet on this VM)
