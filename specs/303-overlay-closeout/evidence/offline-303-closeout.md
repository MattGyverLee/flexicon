# Issue #303 close-out -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/303-overlay-closeout-sep24  
**run_mode:** mock (no FieldWorks on cloud agent)

## Command

```
python3 -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q
```

## Result

7 passed (includes `test_issue303_get_sequence_raises_for_unordered_overlays_oc`).

Prior tranches (#309 Create/GetAll, #384 inherited surface, #364 phantom guards)
unchanged; verified by existing ratchets in the same test module.

**Live:** FAIL: unverified on cloud agent (no FieldWorks / `clr`).
