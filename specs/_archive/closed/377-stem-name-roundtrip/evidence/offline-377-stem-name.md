# Issue #377 item 1 -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/377-stem-name-roundtrip  
**run_mode:** offline (cloud agent -- no FieldWorks / pythonnet LCM)

## Command

```
python3 -m pytest tests/operations/test_issue377_stem_name_roundtrip_offline.py -m "not requires_live_project" -q
```

## Result

**PASS.** `1 passed` (offline ratchet).

## Live

**FAIL: unverified** on cloud agent (no Sena 3 `.fwbackup` / no LCM runtime).
When FieldWorks is available:

```
FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue377_stem_name_roundtrip_live.py -m requires_live_project -q
```
