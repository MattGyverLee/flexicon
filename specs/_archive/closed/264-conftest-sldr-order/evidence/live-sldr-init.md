# Live verification -- issue #264 (conftest.py second Sldr.Initialize removal)

**Project:** Target (real, in-place; FLExProject/LexEntryOperations tests also
used a tempdir sandbox copy per `target_sandbox`)
**Fixture:** target_project, target_sandbox (test_target_live_smoke.py); no
project fixture required for the SLDR singleton tests (test_249_sldr_init_live.py)
**Command:**
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_target_live_smoke.py tests/operations/test_249_sldr_init_live.py -m requires_live_project -q
```
**run_mode:** live (confirmed via `tests/live_status.json`)
**Date:** 2026-09-10

## Claim under test
With the second, unguarded `Sldr.Initialize(True)` call removed from
`tests/conftest.py`, the sole surviving init path
(`flexicon/code/FLExInit.py:90`, `IsInitialized`-guarded) still fully
initializes the SLDR in a live session, and no `.ldml.bad` quarantine
files are produced.

## Pre-state (read from LCM / CLR)
- `Sldr.IsInitialized` before the FLExCleanup/FLExInitialize cycle: `True`
  (session fixture `initialize_flex_for_tests` had already brought it up
  via the sole guarded call path).
- `Sldr.LanguageTags.Count` pre-state: `9596`
- `WritingSystemStore` contents on Target before the run:
  `en.ldml`, `etu.ldml`, `idchangelog.xml` -- no `.ldml.bad` files.

## Action
1. Ran the full live smoke suite (`test_target_live_smoke.py`): opens the
   real Target project write-enabled, opens a `target_sandbox` copy
   write-enabled, and does a create/verify/delete round-trip of a
   `TEST_smoke` lexical entry via `LexEntryOperations`.
2. Ran `test_249_sldr_init_live.py`, which directly exercises the guard now
   depended on exclusively:
   - `Sldr.IsInitialized` read back as a genuine CLR bool.
   - `FLExInitialize()` called twice back-to-back -- idempotent, no raise,
     `Sldr.IsInitialized` stays `True`.
   - `FLExCleanup()` called twice back-to-back (the #249 regression pin) --
     no raise, `IsInitialized` goes `True -> False`, then `FLExInitialize()`
     in a `finally:` brings it back up.

## Post-state (re-queried from LCM / CLR)
- Console evidence from the double-cleanup/reinit cycle (`-s` capture):
  ```
  [INFO] pre-state:  IsInitialized=True  LanguageTags.Count=9596
  [INFO] mid-state:  IsInitialized=False after two FLExCleanup() calls, neither raised
  [INFO] post-state: IsInitialized=True  LanguageTags.Count=9596
  ```
- `Sldr.IsInitialized` after the full run: `True` (asserted directly from
  the CLR property, not inferred).
- `tests/live_status.json` -> `"run_mode": "live"`, 6/6 tests recorded
  `"status": "pass"` across `FLExInit` (read), `FLExProject` (read), and
  `LexEntryOperations` (add).
- `WritingSystemStore` directory
  (`C:\ProgramData\SIL\FieldWorks\Projects\Target\WritingSystemStore`)
  contents after the run: still only `en.ldml`, `etu.ldml`,
  `idchangelog.xml`. `find ... -iname "*.ldml.bad"` returned zero matches.

## Cleanup
- `TEST_smoke` entry was created and deleted inside the sandbox test's
  `finally:`/assertion block; entry count returned to its pre-test value
  (asserted in-test).
- `test_249_sldr_init_live.py`'s autouse `restore_session_sldr` fixture and
  the test's own `finally:` left the session-wide SLDR initialized
  (`Sldr.IsInitialized is True` at session end).
- `python scripts/restore_target.py --check` after the run: Target present,
  not locked; no restore action was necessary since no in-place project
  data was altered on the real Target (only the sandbox copy's LexEntry
  round-tripped, and it self-restored).

## Result
[PASS] -- 6/6 live tests passed, `run_mode: live`, `Sldr.IsInitialized`
read back `True` pre- and post-run, `LanguageTags.Count` unchanged
(9596 -> 9596) across a forced cleanup/reinit cycle, and no `.ldml.bad`
files appeared in the Target's `WritingSystemStore`. The sole
`IsInitialized`-guarded init path in `FLExInit.py` is sufficient with the
second conftest.py call removed.

## Cycle 3 -- offline gate + test_FLExProject live confirmation

**Date:** 2026-09-10
**Change under test:** `@pytest.mark.requires_live_project` added to
`test_AllProjectNames` in `flexicon/tests/test_FLExProject.py`, plus a
docstring note in `tests/test_264_sldr_single_init_path.py` (no code
change -- this cycle verifies the marker, does not fix anything).

### 1. Offline gate

**Command:**
```
python -m pytest -m "not requires_live_project" -q
```
**Result:** `1779 passed, 737 deselected, 12 warnings in 18.67s` -- **0 failed.**

Baseline before this fix was `1 failed, 1779 passed, 736 deselected` (the
one failure being `test_AllProjectNames`, which crashed offline because it
calls `FwDirectoryFinder.ProjectsDirectory` without a live FLEx init).
After the fix: pass count unchanged (1779), deselected count went from 736
to 737 (the newly-marked test moved from "failing" to "correctly
deselected"). Offline gate: **PASS.**

### 2. Live gate for `test_FLExProject.py`

**Command as literally specified:**
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q
```
**Result:** `3 failed in 1.2s` -- all three tests raised
`TypeError: Exception has been thrown by the target of an invocation` at
`FwDirectoryFinder.ProjectsDirectory` inside `FLExLCM.GetListOfProjects()`.
`tests/live_status.json` was **not rewritten** by this invocation (its
`run_timestamp` stayed at an earlier run's value) -- this run produced no
evidence at all, live or mock.

**Root cause (harness, not the change under review):** `flexicon/tests/`
is a directory *outside* the `tests/` subtree, and pytest only auto-loads
a `conftest.py` from ancestor directories of the invoked test path.
Running `pytest flexicon/tests/test_FLExProject.py` in isolation never
loads `tests/conftest.py`, so the session-scoped `initialize_flex_for_tests`
autouse fixture (which calls `FLExInitialize()`, sets up the registry path,
and loads SIL assemblies) never runs -- the process reaches the test with
no FieldWorks environment initialized at all, live or mock. This is a
pre-existing, already-documented quirk: `pyproject.toml` lines 84-89
explicitly register the `requires_live_project` marker at the tool level
"because a conftest.py registers markers only for its own directory
subtree. Modules such as `flexicon/tests/test_CustomFields.py` ... live
OUTSIDE the root `tests/` tree." It is not a regression introduced by
this cycle's change.

**Corrected invocation (loads the same fixture explicitly as a plugin):**
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q -p tests.conftest
```
**Result:** `3 passed in 3.82s`. Console shows the full live init sequence
(`[OK] FieldWorks path added...`, `[OK] FLExInitialize() complete`,
`[OK] Loaded 59/59 operations classes`).

`tests/live_status.json` after this run:
```json
{
  "run_mode": "live",
  "run_timestamp": "2026-09-10T16:55:51Z",
  "by_test": {
    "flexicon/tests/test_FLExProject.py::TestFLExProject::test_AllProjectNames": {"status": "pass", "duration_seconds": 0.012},
    "flexicon/tests/test_FLExProject.py::TestFLExProject::test_OpenProject": {"status": "pass", "duration_seconds": 2.215},
    "flexicon/tests/test_FLExProject.py::TestFLExProject::test_ReadLexicon": {"status": "pass", "duration_seconds": 0.498}
  }
}
```
`run_mode: "live"` -- confirmed. All three tests in the file, including
the newly-marked `test_AllProjectNames`, were selected and PASSED against
a real FieldWorks environment. No project was opened write-enabled
(`test_OpenProject`/`test_ReadLexicon` both call `OpenProject(...,
writeEnabled=False)`); no restore script was run; nothing was written to
any project.

### Verdict
[PASS] -- Offline gate: 0 failed (1779 passed, 737 deselected). Live gate:
3/3 passed with `run_mode: live` once the pre-existing conftest-subtree
harness quirk is worked around with `-p tests.conftest` (documented above;
not a defect in the change under review). The `requires_live_project`
marker on `test_AllProjectNames` is the correct remedy, not a way of
hiding a real failure: the test genuinely passes live.

**Note for the crew:** the literal command
`pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q`
(no `-p tests.conftest`) silently fails to initialize FLEx and produces
neither a live nor a mock result -- it errors out before either fixture
path engages, and does not update `live_status.json`. This is worth a
follow-up issue so a future verifier doesn't mistake that failure mode for
"live FieldWorks itself is broken."
