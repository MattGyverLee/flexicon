# Live verification -- issue #359 anthropology GSP

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue359_anthropology_gsp_live.py -m requires_live_project -q
```

## run_mode

**FAIL: unverified** -- Cloud Agent Linux pod has no FieldWorks LCM runtime.

## Pre-state

`GetSyncableProperties` used `hasattr` on `AnthroCode` and `CategoryRA`; both
guards were always false on `ICmAnthroItem`, so `AnthroCode` was always `None`
even when OCM data was stored in `Abbreviation`.

## Post-state (expected when live runs)

Re-read `GetSyncableProperties` on items with non-empty abbreviation; `AnthroCode`
key matches abbreviation text; `Category` remains `None`.

## Result

**FAIL: unverified** (live LCM read-back not performed in this environment).
