# Live verification -- issue #840 InflectionClassDelete HVO

## Commands

```bash
python3 -m pytest tests/operations/test_issue840_inflclass_delete_hvo_offline.py -m "not requires_live_project" -q
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue840_inflclass_delete_hvo_live.py -m requires_live_project -q
```

## run_mode

`mock` (cloud agent VM: no pythonnet `clr` / FieldWorks)

## Offline

PASS: 3/3 (2026-11-02)

## Live

FAIL: unverified -- `ModuleNotFoundError: No module named 'clr'`; cannot open LCM.

## LCM read-back

Not performed (live blocked).
