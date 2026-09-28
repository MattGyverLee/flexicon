# Issue #492 -- offline evidence (cron close-out)

## Command

```
python3 -m pytest tests/operations/test_issue492_possibility_resolver_cast_offline.py -m "not requires_live_project" -q
```

## Environment

Cursor cloud agent (Linux), 2026-09-25. Behaviour unchanged since PR #496;
this run re-confirms the offline ratchet before closing #492.

## Result

See pytest exit code captured in the close-out commit message / PR body.

## Live

```
FLEXLIBS_REQUIRE_LIVE=1
python3 -m pytest tests/operations/test_issue492_possibility_resolver_cast_live.py -m requires_live_project -q
```

**FAIL: unverified** on this runner (no FieldWorks). Prior record:
`specs/492-possibility-resolver-cast/evidence/live-492.md`.
