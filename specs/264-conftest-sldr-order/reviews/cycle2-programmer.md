# Cycle 2 -- Programmer report: issue #264

## Task A -- skipped per coordination with concurrent #296 session

Investigated first: `tests/contract/snapshots/expected_contract.json`'s diff
(+106/-15) is legitimate work from a concurrent, separately-tracked task
(`specs/296-contract-snapshot-regen/reviews/cycle1-programmer.md` exists in
the shared tree, cross-checked against issue #296's own 2026-09-09
measurement, byte-identical/deterministic). It is not #264 drift. I had
already run `git stash push -- <file>` + `git stash drop` (functionally
equivalent to `git checkout --`) before the coordinator's correction
arrived, confirming offline `test_lcm_contract.py` still passes (22/22)
either way. By the time I re-checked, the file was back in its modified
state -- the concurrent #296 session appears to have rewritten it. **No
further action taken on this file**, per the correction. Current file state
is the concurrent session's, untouched by me since.

## Task B -- 3 markers added, matching test_base_operations.py's style, citing #264

- `flexicon/tests/test_FLExInit.py` -- module-level `pytestmark`, since
  `FLExInitialize()/FLExCleanup()/FLExInitialize()` runs at class scope.
- `flexicon/tests/test_FLExProject.py` -- per-method
  `@pytest.mark.requires_live_project` on `test_OpenProject` and
  `test_ReadLexicon` only; `test_AllProjectNames` left unmarked per the
  audit's scoping (see finding below -- this call chain also proved to be
  live-touching).
- `tests/test_pattern_writing_systems_enumeration.py` -- class-level
  `@pytest.mark.requires_live_project` on `TestWritingSystemsLiveSmoke`
  only; the static-scanner class above it stays unmarked.

## Task C -- ratchet widened

`tests/test_264_sldr_single_init_path.py`: replaced the
`_SYNC_TESTS_DIR`/`"OpenProject("`-only scan with an AST-based scan across
`tests/` and `flexicon/` (`test_*.py`), keying on real `Call` nodes for
`OpenProject`/`FLExInitialize` and on function/method parameters named
`target_project`/`target_sandbox`/`sena3_sandbox` (fixture injection, not
`self.attr = Mock()`). Explicit allowlist with per-entry reasons: the 5
Mock()-based sync files, `test_headless_lcm_ui.py`, and
`test_issue272_service_locator_seam.py` (all per the audit), plus one I
found while widening: `tests/test_249_sldr_init_guard.py`, which calls
`FLExInit.FLExInitialize()` but fully monkeypatches every CLR touchpoint
(documented in its own module docstring) -- adding the marker there would
be wrong, it would exclude a deliberately-offline regression test.

**Proof:** stashed Task B's 3 marker files -> ratchet FAILED, listing all
3 by path. Popped the stash -> ratchet PASSED (2 passed).

## Full offline suite

`python -m pytest -m "not requires_live_project" -q`:
**1779 passed, 736 deselected, 1 failed** (cycle 1: 1784 passed / 732
deselected / 0 failed). Deselected +4 matches the 4 newly-marked tests
exactly.

**Finding -- 1 failure, not caused by this cycle's edits:**
`flexicon/tests/test_FLExProject.py::TestFLExProject::test_AllProjectNames`
now fails: `FwDirectoryFinder.ProjectsDirectory` throws
`TypeError: Exception has been thrown by the target of an invocation.`
Verified independent of my changes: reproduces in isolation, and still
reproduces with `tests/conftest.py` and all Task B markers stashed back to
their pre-cycle-2 state. Root cause is environmental, not code -- likely
contention from the concurrent #296 session also exercising live
FieldWorks/liblcm in this shared machine. Note `AllProjectNames()` itself
touches real `FwDirectoryFinder` state, so it may be a 4th genuine gap
(untouched here -- out of this cycle's ruled-in-scope list of 3).
