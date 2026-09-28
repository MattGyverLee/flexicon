# Issue #258 -- offline verification

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue258_set_infl_aff_msa_slots_offline.py -q
```

**Result:** 4 passed.

**run_mode:** N/A (source ratchets only; no LCM session).

**Pre/post LCM:** not applicable.
