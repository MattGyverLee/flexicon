# Live verification: MorphRuleOperations.Delete helper split (4.13.1 gate)

Change: `__RemoveMemberByHvo` split into `__FindMemberByHvo` (lookup only); the
`.Remove` now runs inline inside each caller's `_TransactionCM` bracket.

Command:
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue802_morphrule_delete_hvo_live.py -m requires_live_project -q

run_mode (tests/live_status.json): live
Fixture: target_sandbox (tempdir copy of Target backup)
Pre-state / post-state: read back from the LCM by the test via
`GetAllCompoundRules()` -- count == before - 1 after Delete, and no remaining
rule has the deleted HVO.
Result: PASS (1 passed)

Offline gate: python -m pytest -m "not requires_live_project" -q
Result: 3944 passed, 0 failed.
