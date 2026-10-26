# Issue #662 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue662_possibilitylist_duplicate_hvo_live.py -m requires_live_project -q
```

**run_mode:** not live (FLEx init failed -- no compatible .NET runtime on cloud agent).

**Result:** FAIL -- unverified. Live gate module is present; Windows/FieldWorks CI or local run required to satisfy write-path verification.
