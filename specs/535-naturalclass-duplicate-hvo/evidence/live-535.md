# Live evidence -- issue #535

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue535_naturalclass_duplicate_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified (cloud agent has no `clr` / FieldWorks)

**run_mode:** not live (FLEx init failed before project open)

**Note:** Live gate module is present for Windows/FieldWorks CI or developer machines with LCM.
