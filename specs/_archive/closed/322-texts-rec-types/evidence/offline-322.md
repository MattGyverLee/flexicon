# Issue #322 -- offline evidence

## Command

```
python -m pytest tests/operations/test_issue322_text_links_offline.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

```
python3 -m pytest tests/operations/test_issue322_text_links_offline.py -m "not requires_live_project" -q
# 3 passed
```

**Pass/fail:** PASS offline. Live LCM not available on this host.

## Behaviour

| Area | Before | After |
|------|--------|-------|
| `GetAllRecordTypes` | `hasattr(lp, RecTypesOA)` always false | `ResearchNotebookOA.RecTypesOA` |
| `LinkToText` / `GetTexts` | `TextsRC` guard, silent no-op | `TextRA` read/write |
| `Anthropology.AddText` | `hasattr(TextsRC)` silent no-op | `FP_ParameterError` |

**Live LCM:** not run on this host (no FieldWorks / `clr`).
