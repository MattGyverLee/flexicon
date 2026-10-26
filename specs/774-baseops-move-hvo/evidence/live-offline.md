# Issue #774 -- offline verification evidence

**Command:**

```
python -m pytest tests/operations/test_issue774_baseops_move_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks/clr)

**Result:** PASS (offline ratchet)

**Live:** FAIL: unverified -- `FLEXLIBS_REQUIRE_LIVE=1` not runnable without clr on this agent.
