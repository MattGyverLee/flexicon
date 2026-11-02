# Cycle 6 - #830 AllomorphOperations inflection classes (lex programmer)

Files changed:
- flexicon/code/Lexicon/AllomorphOperations.py (Get/Add/RemoveInflectionClass, 2 private helpers, import `IMoAffixForm`)
- flexicon/code/Lexicon/AllomorphOperations.pyi (comment only)
- tests/operations/test_issue740_allomorph_rc_hvo_offline.py (affix-path assertions)
- tests/operations/test_issue740_allomorph_rc_hvo_live.py (inflection test rewritten onto affix path)
- NEW tests/operations/test_issue830_allomorph_inflection_class_offline.py (16 tests)
- NEW tests/operations/test_issue830_allomorph_inflection_class_live.py (3 tests)

Behaviour: MoAffixAllomorph / MoAffixProcess are cast locally with IMoAffixForm. Get returns the classes, or [] for stem or other classes. Add is idempotent by HVO, with the check outside _TransactionCM. Remove matches by HVO and is a no-op if absent. MoStemAllomorph Add/Remove raise FP_ParameterError naming project.MSA.SetInflectionClass(msa, infl_class). Any other class raises FP_ParameterError. The shared resolver is untouched. Docstrings are inverted; the FLEx UI label is not stated.

Live: 5 passed (830 live 3 + 740 live 2), FLEXLIBS_REQUIRE_LIVE=1, tests/live_status.json run_mode = "live".
[EVIDENCE] affix allomorph hvo=58052, class hvo=152222 (TEST_830):
- RC before=[]
- after add=[152222]
- after second add=[152222]
- after remove=[]
- Stem allomorph hvo=42189: Get == [], Add/Remove raised FP_ParameterError naming SetInflectionClass.

MoAffixProcess: sena3_sandbox has none ("[EVIDENCE] MoAffixProcess present: False"). Offline coverage only. The live test covers it automatically if one appears (no skip).

New imports (contract regeneration): `IMoAffixForm` from SIL.LCModel in AllomorphOperations.py. Contract test test_no_new_type_dependencies fails, as expected.

Offline run: 3968 passed, 38 failed, 1301 deselected. Failures, none fixed by me:
- tests/contract: test_no_new_type_dependencies (expected, snapshot regeneration).
- tests/operations/test_issue581_offline.py (35 tests): caused by my change. Its stub SIL.LCModel lacks `IMoAffixForm` (ImportError on module load). Integration must add "IMoAffixForm" to its stub attr list. Also its test_get_infl_classes_non_stem and test_add/remove_infl_class_non_stem encode the old stem-only behaviour and need rewriting; its `_make_stem_allomorph` fixtures for the infl-class trio need affix-form equivalents.
- test_issue357_clause_marker_getwordgroup_offline (2) and test_issue471_lexicon_media_move_offline (1): other programmers' files, unrelated to #830.
