# Issue #794 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue794_environment_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (no `clr` / FieldWorks on cloud VM)

**Pre-state / post-state:** not measured on this runner.
