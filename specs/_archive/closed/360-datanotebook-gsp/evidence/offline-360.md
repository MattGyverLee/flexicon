# Issue #360 -- offline verification

**Date:** 2026-09-24  
**Branch:** fix/360-datanotebook-gsp

## Commands

```
python3 -m pytest tests/test_syncable_properties_member_ratchet.py tests/operations/test_issue360_datanotebook_gsp_offline.py -m "not requires_live_project" -q
```

## Result

`76 passed` (member ratchet + issue #360 offline locks), cloud agent, 2026-09-24.
`run_mode`: not applicable (no LCM import in these tests).

## Live

**FAIL: unverified** on cloud agent (no FieldWorks / pythonnet). Re-run:

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue360_datanotebook_gsp_live.py -m requires_live_project -q
```
