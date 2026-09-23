# Issue #305 -- complex form types accessor (offline evidence)

## Commands

```
python3 -m pytest tests/operations/test_issue305_complex_form_types_offline.py -m "not requires_live_project" -q
python3 -m pytest tests/operations/test_collection_cast_pattern.py -m "not requires_live_project" -q -k LexEntryOperations
```

## Result (cloud agent, Linux, 2026-09-23)

Recorded after implementation; see pytest output in PR verification.

## Behaviour

| API | Before | After |
|-----|--------|-------|
| `project.LexEntry.GetAllComplexFormTypes()` | missing; callers used `project.lexDB.ComplexEntryTypesOA` | Yields types from `ComplexEntryTypesOA` with `cast_to_concrete` |
| `project.LexEntry.FindComplexFormType(name)` | missing | Case-insensitive name search over that list |

**Live:** FAIL: unverified on cloud agent (no FieldWorks / `clr`).
