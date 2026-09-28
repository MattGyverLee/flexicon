# Issue #362 -- live evidence

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue362_person_gsp_live.py -m requires_live_project -q
```

## Result (cloud agent, Linux, 2026-09-23)

**FAIL: unverified** -- `FLEXLIBS_REQUIRE_LIVE=1` refused mock fallback:
FLEx/.NET initialization failed (`Failed to create a default .NET runtime`).

## Required follow-up (Windows + FieldWorks)

Re-run the command above; `tests/live_status.json` must show `"run_mode": "live"`.
For each person in Sena 3 sandbox, `GetSyncableProperties` must return a dict
without a `Languages` key and must not raise.
