# Issue #537 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue537_morphrule_duplicate_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (no clr / FieldWorks in cloud agent environment)

**Expected post-state when run on a FieldWorks host:** duplicate HVO appears immediately after source template HVO in `AffixTemplatesOS` order when duplicating via `project.Object(hvo)`.
