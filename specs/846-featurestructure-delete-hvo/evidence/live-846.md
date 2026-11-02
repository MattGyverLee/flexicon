# Live verification: issue #846

**Command (offline):**

```
python3 -m pytest tests/operations/test_issue846_featurestructure_delete_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (cloud agent; no FieldWorks / `clr` on this VM).

**Command (live):**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue846_featurestructure_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (no live LCM in cloud environment).

**Pre-state / post-state:** Not exercised on live LCM in this run.

**Pass/fail:** Offline ratchet PASS; live FAIL: unverified.
