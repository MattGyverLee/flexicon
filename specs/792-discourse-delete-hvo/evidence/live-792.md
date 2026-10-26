# Issue #792 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue792_discourse_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud VM has no `clr` / FieldWorks)

**Pre-state / post-state:** Not measured on this host.

**Result:** FAIL: unverified — live LCM write-path verification blocked (no FieldWorks).
