# Issue #818 offline evidence

## Command

```
python -m pytest tests/operations/test_issue818_datanotebook_delete_hvo_offline.py -m "not requires_live_project" -q
```

## Result

PASS (3/3) — cloud agent, no FieldWorks.

## run_mode

N/A (offline ratchet only).
