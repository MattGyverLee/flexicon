# Issue #597 live verification evidence

**Command (offline gate):**

```
python3 -m pytest tests/operations/test_issue597_variant_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

**Command (live, required for write-path):**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue597_variant_duplicate_hvo_live.py -m requires_live_project -q
```

**run_mode:** `mock` (no `clr` / FieldWorks on cloud agent VM)

**Pre-state / post-state (LCM read-back):** Not executed -- live suite could not run.

**Result:** FAIL: unverified (environment lacks pythonnet FieldWorks stack)
