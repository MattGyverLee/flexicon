# Issue #476 -- offline evidence (cron)

**Date:** 2026-09-25  
**Host:** cloud agent (no libmono / no FieldWorks)

## Commands

```bash
python3 -m pytest tests/operations/test_issue357_clause_marker_getwordgroup_offline.py tests/operations/test_issue476_sysmodules_pollution_offline.py -m "not requires_live_project" -q
```

## Result

**PASS** 6/6 (issue357 + issue476 ratchet)

## Notes

- Order-sensitive regression (`test_issue357` then `test_lexentry_operations` inheritance) not re-run here: those tests import real `flexicon` and require .NET on this host; the pollution failure mode on Windows is documented in #476 and addressed by monkeypatch teardown.
