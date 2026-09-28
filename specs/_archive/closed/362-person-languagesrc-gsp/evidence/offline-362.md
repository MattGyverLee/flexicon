# Issue #362 -- offline evidence

## Commands

```
python3 -m pytest tests/operations/test_person_syncable_properties_offline.py -m "not requires_live_project" -q
python3 -m pytest tests/test_syncable_properties_member_ratchet.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

75 passed (person offline ratchets + full member ratchet suite in one run).

## Behaviour

| Method | Before | After |
|--------|--------|-------|
| `GetSyncableProperties` | `hasattr(person, "LanguagesRC")` always false; `Languages` key never emitted | No `LanguagesRC` reference; RC fields `Positions` / `PlacesOfResidence` unchanged |

**Pass/fail:** PASS offline. Live LCM not available in cloud agent (no .NET runtime / FieldWorks).
