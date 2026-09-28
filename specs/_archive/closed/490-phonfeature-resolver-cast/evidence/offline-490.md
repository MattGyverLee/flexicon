# Issue #490 -- offline verification evidence

**Command:**

```
python -m pytest tests/operations/test_issue490_phonfeature_resolver_cast_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (2/2)

**Pre-state:** `__ResolveObject` returned bare `project.Object(hvo)` on the int path.

**Post-state (source):** int and object paths route through `cast_to_concrete`.

**Live:** FAIL: unverified (no live LCM in cloud environment).
