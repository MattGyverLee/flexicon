# Live evidence: issue 600 (WordformOperations str argument)

Command (PowerShell: `$env:FLEXLIBS_REQUIRE_LIVE = "1"`):
`python -m pytest tests/operations/test_600_wordform_str_arg_live.py -m requires_live_project -q`

run_mode (tests/live_status.json): `live`
Fixture: `target_sandbox` (tempdir copy of Target .fwbackup)

Pre-state: Create("TEST_issue600_wordform") -> wordform exists.
- GetForm("TEST_issue600_wordform") -> FP_ParameterError naming IWfiWordform / Wordforms.Find (was raw AttributeError)
- SetForm(str, "x") -> FP_ParameterError
- Find(...) then GetForm(found) and GetForm(wf.Hvo) -> "TEST_issue600_wordform" (read back from LCM)
Post-state: Delete(wf); Find(...) is None (re-queried).

Result: PASS (1 passed). Offline: 2797 passed, 1111 deselected.
