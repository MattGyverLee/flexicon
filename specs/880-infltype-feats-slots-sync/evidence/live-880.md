# Live verification -- issue #880

**run_mode:** mock (cloud agent -- no FieldWorks/clr)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue880_infltype_feats_slots_sync_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified -- live LCM not available in this environment.

**Offline gate:**

```
python3 -m pytest tests/operations/test_issue880_infltype_feats_slots_sync_offline.py tests/operations/test_issue878_infltype_gloss_sync_offline.py -m "not requires_live_project" -q
```

**Result:** 5 passed
