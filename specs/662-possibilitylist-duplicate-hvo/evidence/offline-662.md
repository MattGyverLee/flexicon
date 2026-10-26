# Issue #662 -- offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue662_possibilitylist_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS -- 2 passed (2026-10-23, cloud worktree `.worktrees/fix-662-possibilitylist-duplicate-hvo`).

**Live LCM:** FAIL -- unverified (no .NET/FLEx runtime on cloud agent; `FLEXLIBS_REQUIRE_LIVE=1` refused mock fallback).
