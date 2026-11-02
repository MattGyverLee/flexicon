# Cycle 7 lex-programmer report (QC P2-1, P2-3, P3-1)

All files edited with CRLF preserved. No code logic changed.

## New constant (ExampleOperations.py:49-59)
_EXAMPLE_MEDIA_WITHDRAWN =
 "ExampleOperations media methods (GetMediaFiles, GetMediaCount, AddMediaFile, RemoveMediaFile, MoveMediaFile) are withdrawn: ILexExampleSentence has no media collection. In surveyed projects FLEx stores example audio as a file name in the audio writing-system alternative of the Example field; writing that alternative with ExampleOperations.SetExample(example, text, wsHandle) is the expected route (not yet exercised by flexicon tests). Dedicated audio methods are planned for 4.14.0; these methods are removed in 5.0."
Substrings required by test_issue831 (:92) are retained.

## Changes
- flexicon/code/Lexicon/ExampleOperations.py: constant (49-59); GetMediaFiles docstring ~1202 ("In surveyed projects ..."); its Notes ~1230 ("expected (not yet tested) way"); AddMediaFile Notes ~1312 (hedged "expected route (not yet exercised by flexicon tests)").
- tests/operations/test_issue830_allomorph_inflection_class_live.py:112 docstring now says MoAffixProcess is UNTESTED live (Sena 3 has none); prints presence and returns if none, round trip only if a fixture gains one. Logic unchanged.
- flexicon/code/Lexicon/AllomorphOperations.py: "offline-tested only; no live fixture contains one" added at 1635, 1663, 1687, 1715, 1751 (docstrings only).
- flexicon/code/Discourse/ConstChartClauseMarkerOperations.py: `import logging` moved to line 14 (top of import block); `logger = ...` at 33 right after imports. except Exception blocks untouched.

## Pytest
python -m pytest tests/operations/test_issue831_example_media_offline.py tests/operations/test_issue830_allomorph_inflection_class_offline.py tests/operations/test_issue832_dependent_clause_rows_offline.py tests/test_docstring_example_ratchet.py -m "not requires_live_project" -q
Result: 59 passed in 6.62s
(Note: this run rewrote tests/test_results.json, a pytest side effect.)
