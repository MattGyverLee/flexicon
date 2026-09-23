# Issue #350 -- offline evidence

## Commands

```
python -m pytest tests/operations/test_agent_syncable_properties_offline.py -m "not requires_live_project" -q
python -m pytest tests/test_syncable_properties_member_ratchet.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

75 passed (agent offline ratchets + full member ratchet suite in one run).

## Behaviour

| Method | Before | After |
|--------|--------|-------|
| `GetSyncableProperties` | Inherited possibility reader; `item.Description` -> `AttributeError` | Agent-specific: `Guid`, `Name`, `Human`, optional `Version` |
| `GetDescription` | Inherited; `item.Description` -> `AttributeError` | Returns `""` |
| `SetDescription` | Inherited; would write `Description` | Validated no-op |

**Pass/fail:** PASS offline. Live LCM not available in cloud agent (`No module named 'clr'`).
