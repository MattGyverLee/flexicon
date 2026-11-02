# Live evidence: #724 (and #774 co-run)

Command:
    $env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_issue724_lexsense_anthrocode_hvo_live.py tests/operations/test_issue774_baseops_move_hvo_live.py -m requires_live_project -q

run_mode (tests/live_status.json, read right after the live run): "live"
Fixture: sena3_sandbox (tempdir copy of Sena 3 .fwbackup). Sandbox had no
anthropology codes, so a TEST_724_code item was created via Anthropology.Create.

State read back from the LCM (sense.AnthroCodesRC re-queried after each step):
- pre-state  (after sense create):                 AnthroCodesRC HVOs = []
- after AddAnthroCode(sense, code):                AnthroCodesRC HVOs = [26614]
- after RemoveAnthroCode(sense, Object(26614)):    AnthroCodesRC HVOs = []

Result: PASS -- 2 passed in 13.13s (724 and 774), no skips.
