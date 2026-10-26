# Issue #790 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue790_segment_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (no FieldWorks / pythonnet clr on cloud agent VM)

**Result:** FAIL: unverified — live LCM not available in this environment.

**Pre/post LCM readback:** not performed.

**PASS line:** FAIL: unverified (blocker: no clr)
