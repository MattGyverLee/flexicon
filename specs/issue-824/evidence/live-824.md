# Live verification: issue #824 (WireRule multi-element context)

Command (target_sandbox, tempdir copy of Target .fwbackup):

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue824_wirerule_multi_context_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"

Pre-state: PhPhonData.ContextsOS.Count = 0
Action: WireRule(left_context=[NC(A), NC(B)], right_context=[NC(C), NC(D)])
Post-state (re-queried by walking phon.PhonRulesOS -> RHS -> LeftContextOA/RightContextOA):
 - both are PhSequenceContext
 - left MembersRS FeatureStructureRA guids == [A, B] in order
 - right MembersRS FeatureStructureRA guids == [C, D] in order
 - ContextsOS.Count = 4

Before fix (fix reverted): FAIL, System.NullReferenceException at
PhSequenceContext.get_MembersRS().
After fix: 1 passed. Regression: tests/operations/test_phon_rules.py + new test: 13 passed (live).

Result: PASS
