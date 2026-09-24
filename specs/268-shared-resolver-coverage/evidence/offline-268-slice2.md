# Issue #268 slice 2 -- offline evidence

**Date:** 2026-09-24  
**Branch:** `fix/268-resolver-hvo-gate-slice2`

## Command

```
python -m pytest tests/operations/test_issue268_resolver_hvo_gate_offline.py -m "not requires_live_project" -q
```

## run_mode

N/A (offline-only ratchet; no LCM session)

## Result

**PASS:** 1 passed (cloud agent, 2026-09-24)

## Live follow-up

When FieldWorks is available:

```
FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue268_resolver_hvo_gate_live.py -m requires_live_project -q
```

Expect `tests/live_status.json` with `"run_mode": "live"`. Cloud agent: **FAIL: unverified**.
