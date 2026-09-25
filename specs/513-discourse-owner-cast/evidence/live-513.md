# Live verification evidence -- issue #513

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue513_discourse_owner_cast_live.py -m requires_live_project -q
```

**run_mode:** mock refused (FLEXLIBS_REQUIRE_LIVE=1, no `clr` / FieldWorks on cloud pod)

**Pre/post LCM:** not measured

**Pass/fail:** FAIL: unverified (environment blocker)
