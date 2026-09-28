# Issue #543 live evidence

**Command (maintainer, Windows + FieldWorks):**

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue543_get_infl_aff_msa_slots_live.py -m requires_live_project -q
```

**Cloud agent result:** FAIL: unverified (no FieldWorks / pythonnet clr in this environment).

**run_mode:** not recorded (live suite not executed here)
