# Issue #350 -- offline evidence

## Lex-lead ruling

See `specs/350-agent-gsp/rulings.md`.

## Commands

```
python -m pytest tests/operations/test_issue350_agent_gsp_offline.py -m "not requires_live_project" -q
python -m pytest tests/operations/test_issue350_agent_gsp_live.py -m requires_live_project -q
```

## Result (cloud agent, 2026-09-23)

```
python3 -m pytest tests/operations/test_issue350_agent_gsp_offline.py -m "not requires_live_project" -q
```

```
3 passed
```

**Live LCM:** not run on this cloud pod (no FieldWorks). Existing live test:
`tests/operations/test_issue350_agent_gsp_live.py` (`sena3_sandbox`).

## Pre/post behaviour

| Check | Before (issue report) | After (main + this PR) |
|-------|----------------------|-------------------------|
| `GetSyncableProperties(agent)` | `AttributeError: ... Description` | Returns dict with `Guid`, `Human`, optional `Name`/`Version`; no `Description` key |
| `GetDescription(agent)` | Inherited possibility path | Returns `""` |
| `SetDescription(agent, ...)` | Would touch missing member | Validated no-op |

**Pass/fail:** PASS offline when pytest green.
