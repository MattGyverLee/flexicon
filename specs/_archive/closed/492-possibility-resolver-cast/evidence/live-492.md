# Issue #492 -- live verification

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue492_possibility_resolver_cast_live.py -m requires_live_project -q
```

**Environment:** Cursor cloud agent (Linux); no FieldWorks / `clr` module.

**run_mode:** Not live -- `FLEXLIBS_REQUIRE_LIVE=1` raised `UsageError` at
collection (refused mock fallback).

**Result:** **FAIL: unverified** on this runner. Gates are in place for
Windows CI / local live runs (`target_sandbox`).
