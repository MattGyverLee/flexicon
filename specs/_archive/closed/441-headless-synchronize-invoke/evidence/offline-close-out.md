# Issue #441 close-out -- offline evidence

**Date:** 2026-09-24  
**Command:**

```
python3 -m pytest tests/test_headless_lcm_ui.py -q
```

**Environment:** Cloud agent (no FieldWorks / pythonnet assemblies).

**Result:** `2 passed, 22 skipped` in 0.09s

**Notes:** Skips are expected when `SIL.LCModel` is unavailable; the two
executed tests are the static / non-LCM slices. Full ILcmUI surface tests
require live pythonnet (FieldWorks install).

**Live LCM:** not run (`run_mode` not applicable -- no `tests/live_status.json`
live session on this host).

**Pass/fail:** Offline gate **PASS** (within cloud constraints). Live **FAIL:
unverified**.
