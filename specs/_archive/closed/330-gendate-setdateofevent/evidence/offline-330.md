# Issue #330 -- SetDateOfEvent GenDate fix (offline evidence)

## Lex-lead ruling

See `../rulings.md`.

## Commands

```
python -m pytest tests/operations/test_issue330_setdateofevent_gendate.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux)

**FAIL: unverified** -- pythonnet cannot load `clr` without a .NET runtime on
this host. Code and mock tests are committed; run the command on a Windows /
FieldWorks machine for machine-checkable evidence.

## Pre/post behaviour (code review)

| Input | Before (assignment) | After |
|-------|---------------------|-------|
| `"2024-01-15"` | `System.DateTime` via Parse -> TypeError on GenDate setter | `"2024-01-15"` string |
| `DateTime(2024,1,15,...)` | `DateTime` instance -> TypeError | normalized string |

**Pass/fail:** logic + tests committed; offline pytest gate not run on this agent.

Live write-path verification (Target sandbox, read-back `DateOfEvent` after
`SetDateOfEvent`) is recommended on a FieldWorks host but was not executed here.
