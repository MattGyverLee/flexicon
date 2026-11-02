# Live verification -- issue #850

**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue850_infl_createvalue_except_live.py -m requires_live_project -q`

**run_mode:** mock (no `clr` / FieldWorks in cloud agent)

**Result:** FAIL: unverified -- live LCM write path not exercised in this environment.

**Pre/post LCM readback:** N/A
