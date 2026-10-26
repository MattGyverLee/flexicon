# Issue #818 live evidence

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue818_datanotebook_delete_hvo_live.py -m requires_live_project -q
```

## Result

**FAIL: unverified** — cloud agent has no FieldWorks/pythonnet (`clr`).

## run_mode

Not recorded (`tests/live_status.json` absent in cloud).
