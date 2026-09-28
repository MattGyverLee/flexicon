# Issue #493 -- live verification

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue493_scripture_resolver_cast_live.py -m requires_live_project -q
```

**Environment:** Cursor cloud agent (Linux); no FieldWorks / `clr` module.

**run_mode:** Not live -- `FLEXLIBS_REQUIRE_LIVE=1` refused mock fallback at collection.

**Result:** **FAIL: unverified** on this runner. Gates are in place for Windows CI / local live runs (`sena3_sandbox`).
