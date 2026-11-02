# Cycle 2 - test fixes (lex-programmer)
Offline: 3946 passed. Live (FLEXLIBS_REQUIRE_LIVE=1, run_mode=live): 6 pass/skip, 1 FAIL (#686, library defect).

- 648: module import of IPartOfSpeech moved into the test; also `sandbox.project.lp` -> `sandbox.lp` (FLExProject.lp). Live: 2 passed.
- 686: setup now uses Pronunciations.AddMediaFile with a tmp wav. FAILS: library defect. AddMediaFile (PronunciationOperations.py:769) does MediaFilesOS.Add(ICmFile) -> "No method matches ICollection`1.Add: (ICmFile)". MediaFilesOS holds ICmMedia. MoveMediaFile line 904 does the same Add. Stopped; test left calling the real library path.
- 692: expected order now [s1, s0, default_sense, s2] (default hvo read from entry.SensesOS before creating; Reorder keeps unlisted in original order). Live: pass.
- 724: GetList -> Anthropology.GetAll(). Live: SKIPPED (Target has no anthropology codes), so unverified.
- 774: LexiconEntries -> LexEntry. Then MoveDown returned 0 because the raw sense was last (default sense is first); now creates senses so the raw one is the middle one. Live: pass.
- 804: Exists calls replaced with HVO membership in entry.SensesOS read back. Live: pass.
- 814: helper now reads ref_type.MembersOC HVOs. Live: pass.

Library defects:
1. #686 above (AddMediaFile/MoveMediaFile add ICmFile to MediaFilesOS).
2. LexReferenceOperations.GetAll (lines 689/702/708) uses non-existent ILexSense.ReferringLexReferences, so GetAll always raises.

Note: git diff shows CRLF/other-file churn in tests 664/672/716-744 that I did not touch (line-ending warnings only).
