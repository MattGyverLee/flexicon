# Live evidence: issue #776

Command (worktree flexicon-wt-issues):
    $env:FLEXLIBS_REQUIRE_LIVE="1"; python -m pytest tests/operations/test_issue776_baseops_sort_hvo_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"
Fixture: target_sandbox (tempdir copy of Target .fwbackup)

Test 1 (Sort): pre-order SensesOS HVOs = [c, a, b]; Sort with key_func resolving
via Object(hvo); re-queried post-order = [a, b, c].
Test 2 (_ApplySequenceOrder): desired_order = raw Object(hvo) views [b, a, c];
re-queried post-order = [b, a, c].

Result: 2 passed with fix. NOTE: the same 2 tests also pass against unfixed HEAD BaseOperations, so they do not discriminate the bug in this environment (pythonnet proxies compared equal); they are regression/behavior gates, not a repro.
