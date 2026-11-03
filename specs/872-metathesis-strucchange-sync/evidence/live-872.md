# Live verification -- issue #872

**Command:**

```text
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue872_metathesis_strucchange_sync_live.py -m requires_live_project -q
```

**run_mode:** mock (no FieldWorks/CLR in cloud agent VM)

**Result:** FAIL: unverified -- live LCM write/read not executed.

**Pre/post LCM readback:** N/A (offline-only environment).
