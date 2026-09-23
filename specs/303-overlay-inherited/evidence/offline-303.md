# Issue #303 -- inherited OverlayOperations surface (offline evidence)

## Commands

```
python3 -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

6 passed, 4 deselected (2026-09-23, cloud agent). Source ratchets do not require pythonnet.

## Behaviour

| Method | Before | After |
|--------|--------|-------|
| `Duplicate` | Inherited; `_get_list_object()` None -> error or no-op | Factory + `OverlaysOC.Add`, copy Name/PossListRA/PossItemsRC |
| `GetDescription` / `SetDescription` | `Description.get_String` -> AttributeError | `""` / validated no-op |
| `CompareTo` | `Name.get_String` -> AttributeError | Plain-string `GetName` compare |
| `GetSyncableProperties` | Reads multilingual Description | Guid, Name, PossListRA only |
| `FindByChart` | `chart.OverlaysOC` -> always [] | `GetAll()` (project-scoped) |

**Live:** FAIL: unverified on cloud agent (no FieldWorks / `clr`).
