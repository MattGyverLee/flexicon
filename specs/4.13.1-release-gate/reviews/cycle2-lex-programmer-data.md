# Cycle 2 - data fixes for 9 live tests (lex-programmer)

Dev loop: offline `-m "not requires_live_project"` = 3946 passed. Live run (FLEXLIBS_REQUIRE_LIVE=1, 9 files)
= 11 passed, 1 FAILED, 0 skipped; tests/live_status.json run_mode = "live".

All 9 files switched to `sena3_sandbox` (Sena 3 is Portuguese-localized: 1462 entries, 44 environments,
1 publication, UsageTypesOA 21 items, DomainTypesOA 22 items; no check list, no inflection classes).

- 664 PASS. `Checks._GetCheckList()` is a stub that always returns None; no public accessor exists. Test now reads
  the owning list via `Object(chk_b.Hvo).Owner` cast to ICmPossibilityList; order assertion kept.
  FLAG: library stub / orphan check list (not owned by LexDb).
- 716 PASS (sena3_sandbox only).
- 742 PASS. 744 PASS (2 tests).
- 672 PASS: creates `TEST_672_second_pub` (Sena 3 has 1 publication); skips replaced by asserts.
- 720 PASS: usage type taken from `lexDB.UsageTypesOA` (list name lookup fails on localized names).
- 722 PASS: domain type from `lexDB.DomainTypesOA` (old code used "Semantic Domains", wrong list for DomainTypesRC).
- 738 PASS (2 tests): removed finally-block `UndoableOperation` restore, which raised FP_TransactionError on the
  undoable=False sandbox (sandbox is discarded anyway); no assertions touched.
- 740 envs test PASS. Inflection-class test FAIL - LIBRARY DEFECT, stopped:
  `Allomorphs.AddInflectionClass` (AllomorphOperations.py ~1697) uses `allomorph.InflectionClassesRC`, but
  `IMoStemAllomorph` has no such attribute (AttributeError); the property lives on affix allomorphs. The method
  documents itself as stem-only, so the premise is wrong (also Remove ~1756, Get ~1634). Test prerequisites are
  in place (creates TEST_ IMoInflClass via raw factory; Sena 3 has none; dead `LexEntry.SetPOS` call removed since
  that method does not exist; skips converted to asserts). Needs library fix before this test can pass.
