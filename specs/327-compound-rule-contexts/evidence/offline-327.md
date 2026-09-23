# Issue #327 -- offline verification

**Command:**

```
python3 -m pytest tests/operations/test_issue327_compound_rule_contexts.py tests/test_compound_rule_wrappers.py -m "not requires_live_project" -q
```

**Environment:** cloud agent, 2026-09-23, no FieldWorks/clr.

**run_mode:** not applicable (offline-only tests; no live_status.json write).

**Pre-state:** `CompoundRule.left_context`/`right_context` probed nonexistent
`LeftContextOA`/`RightContextOA` on compound concrete types.

**Post-state (code):** phantom context properties removed; `head_last`,
`overriding_msa`, `to_msa` added per lcm-member-truth-sweep T2.5b.

**Result:** 3 passed (cloud agent, 2026-09-23).

**Live:** FAIL: unverified — no FieldWorks/clr on cloud agent.
