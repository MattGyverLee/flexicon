# Issue #666 offline evidence (cron)

## Command

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue666_annotationdef_duplicate_hvo_offline.py -q
```

## Result

PASS (2/2 offline ratchet tests).

## Live

Not run on this host (no FieldWorks / clr). See `live-666-cron.md`.
