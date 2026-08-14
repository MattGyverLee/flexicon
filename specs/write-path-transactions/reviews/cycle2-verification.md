# Cycle 2 - Verification Agent report

## CLAIM 1 (Track A: 46/46 + zero-regression) - PARTIAL

**Sub-claim "46/46 passed"**: CONFIRMED. Re-ran
`tests/test_headless_lcm_ui.py tests/test_transaction_honesty.py
tests/operations/test_transaction_rollback.py` -> `46 passed, 1 warning in 1.82s`.

**Sub-claim "1414 passed, 57 failed, 9 skipped"**: REFUTED (numbers wrong).
Actual, working tree, `pytest --ignore=tests/contract -q`:
`139 failed, 1637 passed, 20 skipped, 17 errors, 5 subtests passed` (102.7s).
Not 57/9 by a wide margin, and 17 collection ERRORs (all in
`flexicon/sync/tests/test_duplicate_operations.py`) go unmentioned in the claim.

**Sub-claim "identical failures before/after, verified via git stash"**:
CONFIRMED, independently re-verified. `git stash -u` -> pre-change run:
`139 failed, 1604 passed, 20 skipped, 17 errors` (95.5s) -> `git stash pop`.
Diffed the FAILED and ERROR name sets (not counts) between the two runs:
**both diffs are empty** - the same 139 test IDs fail, and the same 17 error,
before and after. Zero regressions from this change, confirmed by name.
(passed count differs by 33, consistent with the ~34 new tests Track A added.)
`git status --short` after pop matches the pre-stash baseline exactly.

**Sub-claim "all pre-existing stale flexlibs2->flexicon rename path
breakage"**: REFUTED as a blanket statement; TRUE for only a subset.
Spot-checked several failure causes directly:
- `tests/test_write_enabled_fix.py`, `tests/test_itsstring_fix.py`: genuinely
  rename breakage - source literally does
  `Path("flexlibs2/code/BaseOperations.py")` (hardcoded relative path, old
  dir name), `FileNotFoundError` since no `flexlibs2/` dir exists in this repo.
  This category (~15-20 tests: write_enabled_fix, itsstring_fix,
  custom_field_create_refusal, phoneme_duplicate_fix, rule_patterns,
  lcm_method_verification, pattern_writing_systems_enumeration,
  wfianalysis_agent_import, consolidation_coverage) IS rename breakage.
- BUT `tests/operations/test_text_operations.py::...test_create_and_delete_text`
  fails with `FP_ParameterError: A text with the name 'Test Text 123' already
  exists` - a **live LCM run against a real FLEx project** hitting leftover
  state, not a path issue.
- `flexicon/sync/tests/test_diff_engine.py::...test_compare_unchanged_objects`
  fails `AssertionError: 1 != 0` - a genuine sync-engine logic bug, unrelated
  to any rename.
- The 60 `test_duplicate_operations.py` failures/errors and the `test_validation.py`
  / `test_sync_engine.py` failures are Mock-based unit-test breakage
  ("'Mock' object is not iterable") in the `flexicon/sync` package, also
  unrelated to renaming.
- Note: this environment has live pythonnet/LCM available (`import clr`
  succeeds; `FLExInitialize` ran real project operations during the suite,
  including one fatal-looking but non-terminating "Windows fatal exception:
  access violation" in a background thread inside
  `flexicon/sync/tests/test_base_operations.py::setUpModule`). This live-LCM
  dependency most likely explains why my failure count (139) differs so much
  from the claimed 57 - environments differ in what's actually exercised.

**Verdict: PARTIAL.** 46/46 and the zero-regression-by-name claim both hold.
The absolute counts (1414/57/9) and the "ALL pre-existing rename breakage"
characterization are false; the real total is 139 failed/17 errors with mixed
causes (rename breakage + live-LCM state pollution + real sync-engine bugs).

## CLAIM 2 (contract agent: 22/0) - CONFIRMED

`pytest tests/contract/ -q` -> **22 passed, 3 warnings in 2.61s**. Matches
exactly.

`TestTransactionLayerContract` (test_lcm_contract.py:365+) uses the
`baseline_snapshot` fixture, which loads the checked-in
`tests/contract/snapshots/liblcm_baseline.json` and only `pytest.skip()`s if
that file is absent - no live liblcm/FieldWorks call. Confirmed by reading
the fixture (line 125-130) and the file's own comment at line 356-357: "These
tests read the checked-in baseline_snapshot fixture directly (no live liblcm
required -- Mode 1)". Mode 1 confirmed; does NOT require live LCM.

## SOURCE CLAIMS - all CONFIRMED by reading

- `OpenProject(self, projectName, writeEnabled=False, undoable=False, ui=None)`
  at `FLExProject.py:163`; passes `ui` to `FLExLCM.OpenProject(projectName, ui)`
  (`:221`); `FLExLCM.py:98-99` shows `ui=None` -> `FwLcmUI(None, th)`.
- `RefreshFromDisk()` at `FLExProject.py:547-592`: raises `FP_ReadOnlyError` if
  `not self.writeEnabled` (`:588-589`), else calls
  `self.ObjectRepository(IUndoStackManager).Refresh()` (`:591-592`).
- `_GetTransactionAPI` and `"RollbackToMark"`: zero matches anywhere under
  `flexicon/code/` (grepped).
- `headless_ui.py::HeadlessLcmUI`: cross-checked against
  `liblcm/src/SIL.LCModel/ILcmUI.cs` directly - the real interface has exactly
  2 properties (`SynchronizeInvoke`, `LastActivityTime`) and 10 methods
  (`ConflictingSave`, `ChooseFilesToUse`, `RestoreLinkedFilesInProjectFolder`,
  `CannotRestoreLinkedFilesToOriginalLocation`, `DisplayMessage`,
  `ReportException`, `ReportDuplicateGuids`,
  `DisplayCircularRefBreakerReport`, `Retry`, `OfferToRestore`). All 10+2 are
  implemented in `headless_ui.py`, including `RestoreLinkedFilesInProjectFolder`
  (the previously-missing one). `TouchActivity` is an extra convenience method,
  not part of `ILcmUI`. No `.Invoke(` / `.BeginInvoke(` in the file (grepped,
  zero matches).

## Working tree integrity

`git status --short` after the stash/pop cycle matches the pre-verification
baseline exactly (same 11 modified + 5 untracked entries). No commits made.
No live-LCM writes performed by this agent directly; the pre-existing test
suite itself opens/writes to a real FLEx project as part of its own fixtures
(observed, not initiated as a manual action).
