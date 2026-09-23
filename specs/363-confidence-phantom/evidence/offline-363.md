# Issue #363 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue363_confidence_offline.py tests/operations/test_issue272_service_locator_seam.py -m "not requires_live_project" -q
```

**Environment:** cloud agent (Linux), 2026-09-23

**Result:** `2 passed` (issue363 offline ratchets); `test_issue272_service_locator_seam.py` collected with inventory rows for ConfidenceOperations removed (11 passed / 4 failed in combined run on cloud agent -- failures are pre-existing `ModuleNotFoundError: clr` in unrelated #272 seam tests, not this change).

**Pass/fail:** PASS (offline ratchets for #363)
