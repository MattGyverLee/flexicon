# Issue #740 offline evidence

**Command:**

```
cd /workspace/.worktrees/fix-740-allomorph-rc-hvo
python3 -m pytest tests/operations/test_issue740_allomorph_rc_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 3 passed

**run_mode:** mock (offline ratchet only; no LCM)

**Pass/fail:** PASS
