# Live verification: follow-up to #448 (LexiconSetListFieldSingle subclass cast)

Commands (worktree C:/Github/flexicon-448b):

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue448_setlistfield_subclass.py tests/operations/test_issue448_move_item_live.py -m requires_live_project -q -s

run_mode (tests/live_status.json): live

Pre/post values read back from the LCM (target_sandbox, new MoStemMsa):
- pre  PartOfSpeechRA = None
- LexiconSetListFieldSingle(msa, fid, PartOfSpeech obj) -> re-queried PartOfSpeechRA.Guid == pos.Guid
- LexiconClearListFieldSingle -> re-queried PartOfSpeechRA is None
- LexiconSetListFieldSingle(msa, fid, bare ICmObject) -> re-queried PartOfSpeechRA.Guid == pos.Guid
- non-possibility (ILexEntry) -> FP_ParameterError
Also: nested CmSemanticDomain round trip on sena3_sandbox (move to top, back under
parent, already-in-place move) keeps the same GUID.

Negative control: with the old ClassName check restored,
test_set_list_field_single_partofspeech_live FAILED; with the fix it passes.

Result: 4 passed, 8 deselected -- PASS
Offline: full `-m "not requires_live_project"` run has the same 47 pre-existing
failures before and after this change (identical list), 2742 passed.
