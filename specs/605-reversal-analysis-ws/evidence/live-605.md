# Live evidence: issue 605 (ReversalIndexOperations.Create analysis-WS check)

Command (PowerShell: `$env:FLEXLIBS_REQUIRE_LIVE = "1"` first):

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_reversal_index_create_analysis_ws_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"
Fixture: target_sandbox (tempdir copy of the Target .fwbackup)

## Pre/post state read back from the LCM (index list via ReversalIndexes.GetAll())
- Vernacular WS (tag, then int handle): pre = ['en']; Create raised
  FP_ParameterError both times; post = ['en'] (identical, nothing created).
- Analysis WS 'en': Target's only analysis WS already had an index, so the
  sandbox copy's 'en' index was deleted first (re-read: no 'en'), then
  Create("TEST_anal", "en") -> list grew by exactly one and contains 'en'.

Result: PASS (2 passed in 2.22s)
Offline gate: python -m pytest -m "not requires_live_project" -q -> 2794 passed, 1112 deselected
