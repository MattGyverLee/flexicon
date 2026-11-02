# Cycle 6 - #831 Example media withdrawal (programmer)

Files (nothing staged or committed):
- flexicon/code/Lexicon/ExampleOperations.py: five media methods rewritten; `import warnings` and `_EXAMPLE_MEDIA_WITHDRAWN` added (module level). Duplicate note (~line 340) reworded. `.pyi` has no media entries, so it is unchanged.
- tests/operations/test_issue831_example_media_offline.py (new), test_issue831_example_media_live.py (new)
- tests/operations/test_issue684_example_movemedia_hvo_offline.py and _live.py rewritten (they now lock the withdrawn behaviour)

Behaviour:
- All five call warnings.warn(msg, DeprecationWarning, stacklevel=2).
- Add, Remove and Move then raise FP_ParameterError unconditionally, before any CopyToProject, LCM access or transaction (no write-enabled check or capability probe).
- GetMediaFiles returns [] and GetMediaCount returns 0, with no MediaFilesOS probe. FP_NullParameterError on None is kept.
- The message does not claim the audio file's on-disk location.
- Docstrings say the methods are withdrawn and each keeps a valid Example section. tests/test_docstring_example_ratchet.py passes.
- New imports: `warnings` only. `require_lcm_object` is still used elsewhere in the file.

Offline: full run was 3968 passed and 38 failed. My three files and the docstring ratchet pass (34 tests).

Failures NOT fixed:
- tests/operations/test_issue471_lexicon_media_move_offline.py::TestIssue471MoveRatchet::test_move_method_has_no_remove_on_item[example-media] is CAUSED BY THIS CHANGE (1 failure). It asserts `.MediaFilesOS.Add(` is in Example.MoveMediaFile. I do not own the file and have not touched it. Lex-lead should retire or adjust that parametrisation.
- Not caused by this work (34 + 2 + 1 = 37 failures):
  - test_issue581_offline.py: 34
  - test_issue357_clause_marker_getwordgroup_offline.py: 2
  - tests/contract/test_lcm_contract.py: 1
  - These sit alongside other programmers' concurrent edits (ConstChartClauseMarkerOperations.py, FLExProject.py).

Live (FLEXLIBS_REQUIRE_LIVE=1, target_sandbox): 2 passed. tests/live_status.json shows "run_mode": "live".

[EVIDENCE] example HVO 10446. Values were re-queried after `project.Object(hvo)`:

| Stage | ICmFile count | LinkedFiles/AudioVisual | Example multistring |
|---|---|---|---|
| Before | 1 | does not exist (None) | {999000002: 'TEST_831_example'} |
| After AddMediaFile | 1 | None | unchanged |
| Final, after Remove and Move | 1 | None | unchanged |

The final row also had GetMediaFiles == [] and GetMediaCount == 0. Add, Remove and Move each raised FP_ParameterError under a DeprecationWarning.
