# Issue #461 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue461_phonological_rule_resolver_cast_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx/.NET runtime unavailable in cloud pod)

**Pre-state / post-state:** not measured -- initialization failed before LCM access.

**Result:** **FAIL: unverified** (no FieldWorks / Mono runtime on this host)
