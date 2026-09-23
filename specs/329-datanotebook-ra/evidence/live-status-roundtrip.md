# Issue #329 -- live evidence (status round-trip)

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue329_datanotebook_ra.py -m requires_live_project -q
```

## run_mode

From `tests/live_status.json` after the run (see pytest output).

## Pre-state

New `TEST_329_status_roundtrip` record on `target_sandbox`; `GetStatus(hvo)` returned `None`.

## Post-state

After `SetStatus(hvo, chosen)` and re-read by HVO: `GetStatus(hvo).Hvo == chosen.Hvo`;
`GetSyncableProperties(hvo)["Status"] == str(chosen.Guid)`.

## Verdict

See pytest result line below (filled by automation run).
