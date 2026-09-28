# Issue #336 -- empty Guid in PhonFeatureOperations sync (offline evidence)

## Lex-lead ruling (2026-09-23)

**Decision:** When `props["Values"][i]` includes a `"Guid"` key whose value is the
empty string, `ApplySyncableProperties` / `__CreateValueWithGuid` must raise
`FP_ParameterError`. When the `"Guid"` key is **absent**, behaviour is unchanged:
mint a new value with a random GUID (last-resort path).

**Rationale:** An explicit `""` usually means a truncated or lost identity from
upstream serialization, not a deliberate "please mint" request. Silent random
GUID assignment breaks sync round-trips and matches the silent-data-loss class
documented in `specs/tier1-silent-data-loss/`.

## Commands

```
python -m pytest tests/operations/test_issue334_guid_parse_formatexception.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux)

**FAIL: unverified** -- pytest session cannot initialize pythonnet without a
.NET runtime on this host (`RuntimeError: Failed to create a default .NET
runtime`). Code change and test expectation update are committed; a Windows /
FieldWorks environment must run the command above for offline gate evidence.

## Pre/post behaviour (code review)

| Input | Before | After |
|-------|--------|-------|
| `"Guid"` key absent | random GUID mint | unchanged |
| `"Guid": ""` | random GUID mint (silent) | `FP_ParameterError` |
| well-formed GUID | aligned create | unchanged |

**Pass/fail:** logic + test update complete; machine gate not run on this agent.
