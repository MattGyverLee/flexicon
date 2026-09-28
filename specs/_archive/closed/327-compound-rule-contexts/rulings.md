# Issue #327 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/327-compound-rule-contexts from origin/main

## RULING (binding)

Live reflection (lcm-member-truth-sweep T2.5b, issue #327) confirms
`IMoEndoCompound` and `IMoExoCompound` have **no** phonological-context members
under any suffix. This is **not** the #283 `IPhEnvironment` OA→RA rename; a blind
suffix swap would be wrong in both directions.

**Correct LCM surfaces:**

| Type | Members |
|------|---------|
| `IMoEndoCompound` | `HeadLast` (bool), `OverridingMsaOA` (`IMoStemMsa`) |
| `IMoExoCompound` | `ToMsaOA` (`IMoStemMsa`) |

**Fix for this PR:**

1. **Remove** `CompoundRule.left_context`, `right_context`, and `contexts` -- they
   implied a reachable context that LCM never attaches to compound rules.
2. **Add** `head_last`, `overriding_msa`, and `to_msa` on the wrapper (type-gated
   like other compound-specific properties).
3. **Correct** module and collection docstrings that still claimed `LeftContextOA` /
   `RightContextOA`.

**Out of scope:** morph-rule context wiring (`PhonologicalRuleOperations.WireRule`);
that path targets `IPhEnvironment`, not compound rules.

## Verification plan

- Offline: AST ratchet (no phantom `LeftContextOA` in `compound_rule.py`) + unit
  tests for new properties; `test_compound_rule_wrappers.py` collection examples
  updated away from context predicates.
- Live: extend compound-rule live probe when `FLEXLIBS_REQUIRE_LIVE=1` is
  available (cloud agent: FAIL: unverified).
