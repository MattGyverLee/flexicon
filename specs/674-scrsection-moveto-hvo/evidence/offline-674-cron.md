# Issue #674 -- offline evidence (cron 2026-10-23)

## Command

```
python -m pytest tests/operations/test_issue674_scrsection_moveto_hvo_offline.py -m "not requires_live_project" -q
```

## run_mode

Cloud agent: no FieldWorks; offline ratchet only. `tests/live_status.json` not updated (no live run).

## Result

**PASS** — 2 passed in 0.07s (cloud agent cron run)

## Live LCM

**FAIL: unverified** — no clr / FieldWorks on cloud VM. Gate: `tests/operations/test_issue674_scrsection_moveto_hvo_live.py`
