# Live verification -- issue #285 POST-FIX conflict measurement

**Project:** Target (tempdir sandbox copies of the Target `.fwbackup` only --
the real Target project was never opened for writing; confirmed untouched,
see Cleanup)
**Pinned worktree commit:** `452624520aa7eebf9a4da0d1a53bb403fab63775`
(`4526245`, "fix(285): default OpenProject(ui=None) to HeadlessLcmUI, export
it at top level" -- the pure implementation commit). Confirmed
`flexicon/code/FLExLCM.py:99` reads `ui = HeadlessLcmUI()` at this SHA.
**Command:**
```
git worktree add <scratch>/post285 4526245
cp "tests/fixtures/Target 2026-07-06 0218.fwbackup" <scratch>/post285/tests/fixtures/
cd <scratch>/post285
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_285_postfix_conflict_live.py -m requires_live_project -q -s
```
**run_mode:** `live` (`tests/live_status.json`, `run_timestamp:
2026-09-08T21:17:26Z`)
**Date:** 2026-09-08

## Claim under test
Issue #285's fix: `OpenProject(..., ui=None)` now defaults to
`HeadlessLcmUI()`. On a genuine conflicting save it must raise
`FP_ConflictingSaveError` instead of blocking or silently discarding, AND
the exception's own message claim ("This session's unsaved changes were
NOT discarded") must hold under re-query, not just be trusted from the
docstring. An explicit `ui=FwLcmUI(None, ThreadHelper())` opt-out must
still reach the historical path.

## Harness
Reused cycle 1's design: two independent `LcmCache` instances opened
concurrently on the SAME tempdir-sandboxed `.fwdata` file, by
monkeypatching `flexicon.code.FLExLCM.ProjectId` (test-harness-only, never
shipped code) to force `BackendProviderType.kSharedXML`. A seed session
creates `TEST_285_conflict` with `CitationForm="seed_value"`; writer1 and
writer2 both open after the seed closes (so both start from
`seed_value`); writer2 stages an uncommitted edit first; writer1 commits a
conflicting change and saves; writer2 then calls `SaveChanges()` -- the
measurement point. All three sessions run inside one OS-subprocess
(`conflict_worker.py`, not a pytest in-process thread), launched with a
`subprocess.Popen` + timeout wrapper from the pytest test so a genuine
hang cannot wedge the harness; a timeout terminates the child. The
subprocess forces `sys.path` to the PINNED worktree ahead of the ambient
editable install (`pyflexicon` `Location: D:\...\flexicon`, which points
at the concurrently-moving branch checkout) -- verified via
`flexicon.__file__` in the result JSON on every run.

## Pre-state (read from LCM, seed phase)
`TEST_285_conflict` CitationForm: `"seed_value"` (re-read via
`GetCitationForm()` immediately after `SaveChanges()`, before either
writer opened).

## Action / Measurements

### (1) Post-fix `ui=None` -- the fix itself
Writer2's `SaveChanges()` raised:
- **Type:** `FP_ConflictingSaveError`
- **Message:** `"Another client saved conflicting changes to this
  project. This session's unsaved changes were NOT discarded. Close
  without saving, or reopen and re-apply the operation."`

### (2) The claim in HeadlessLcmUI's own message, measured
After catching the exception, writer2's field was re-fetched via a FRESH
`fp2.Object(guid)` call in writer2's still-open session (guid re-query,
not the input value):
- **`post_exception_reread_writer2_field`: `"writer2_value"`** -- the
  session's in-memory edit is still present; `RevertToSavedState()` did
  NOT run. The claim holds.

A genuinely fresh THIRD session, opened only after both writer1 and
writer2 had closed, read the on-disk state:
- **`third_session_disk_value`: `"writer1_value"`**

This matches the expected shape exactly: disk holds `writer1_value` (the
conflict prevented writer2's edit from ever reaching disk, same
observable disk outcome as pre-fix), but the caller was TOLD via an
exception -- confirmed present in writer2's live in-memory session --
rather than losing the write silently with no signal. No contradiction of
the shipped message found.

### (3) Regression -- explicit `ui=FwLcmUI(None, ThreadHelper())` opt-out
Same scenario, writer2 opened with the explicit opt-out. Measured TWICE:
- **Direct-script invocation** (outside pytest): `SaveChanges()` returned
  with **no exception** (`save_exception_type: null`); re-read of
  writer2's field showed `"writer1_value"` -- writer2's edit was silently
  discarded (`RevertToSavedState()` ran). This reproduces cycle 1's
  bare-script finding.
- **Mandated pytest-subprocess invocation**
  (`FLEXLIBS_REQUIRE_LIVE=1 pytest -m requires_live_project`): completed
  in 67.1s (well under the 120s timeout) with the SAME outcome -- no
  exception, silent discard. Did not reproduce cycle 1's >105s block this
  run, but per the task's framing either outcome (silent discard or block)
  is accepted as PASS for "reached the historical path, did not raise
  `FP_ConflictingSaveError`" -- confirmed here as the former. No hung
  process was created or left behind.

## Post-state (re-queried from LCM)
- Measurement (1)/(2) run: disk CitationForm = `"writer1_value"` (3rd
  session read).
- Measurement (3) run: disk CitationForm = `"writer1_value"` (3rd
  session read); writer2's own field read back as `"writer1_value"`
  (discarded).

## Cleanup
- Both tempdir sandboxes created by `target_sandbox_path` (pytest run)
  were deleted by fixture teardown; two additional manual tempdir
  sandboxes used for pre-pytest dry runs were deleted explicitly
  afterward.
- No child processes were left running: the pytest invocation completed
  both tests in 74.17s total with exit status green; process list
  checked post-run and contained only pre-existing, unrelated
  `flextoolsmcp`/`pyright-langserver` processes.
- `python scripts/restore_target.py --check` confirms the real Target
  project was never opened for writing by this measurement.
- Git worktree at `<scratch>/post285` removed
  (`git worktree remove --force`), confirmed via `git worktree list`.
- Sena 3 was not touched at any point.

## Result
[PASS] -- All three measurements confirmed live, re-queried from the
LCM (not asserted on input values). `run_mode: live` confirmed
(`run_timestamp: 2026-09-08T21:17:26Z`). Fix raises
`FP_ConflictingSaveError` with the session's edit intact and disk
integrity preserved (1). The shipped exception message's claim survived
measurement, not refuted (2). The explicit opt-out still reaches the
historical (pre-fix) path (3).
