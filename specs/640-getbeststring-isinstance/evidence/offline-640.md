# Issue #640 offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue640_getbeststring_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (session default; offline ratchet only)

**Result:** PASS -- 2 passed in 0.14s

**Pre/post LCM:** N/A (source ratchet)
