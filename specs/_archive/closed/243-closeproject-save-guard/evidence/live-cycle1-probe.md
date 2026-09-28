# Live verification -- issue #243 CloseProject() save-guard, CHECKPOINT 1 probe

**Project:** Target | **Fixture:** `target_sandbox_path` (fresh tempdir copy
of `tests/fixtures/Target*.fwbackup` per test, `.fwdata` PATH only, project
lifecycle owned by each test -- deleted on teardown, no restore needed,
nothing persisted, the real Target project was never opened or touched)

**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
```

**run_mode:** live (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"` -> `live`,
`run_timestamp: 2026-09-07T08:42:33Z`)

**Date:** 2026-09-07
**Result:** 5 passed

This is a CHECKPOINT 1 probe -- it measures the bug, it does not fix it. No
file under `flexicon/code/` was modified for this task.

## P-1 -- mode matrix

Opened the same sandbox `.fwdata` three times in sequence, one mode each,
reading `writeEnabled` / `_undoable` straight off the live `FLExProject`
after `OpenProject()`:

```
mode a (writeEnabled=True, undoable=default): writeEnabled=True _undoable=True  line326_reached=False
mode b (writeEnabled=True, undoable=False):   writeEnabled=True _undoable=False line326_reached=True
mode c (writeEnabled=False):                  writeEnabled=False _undoable=False line326_reached=False
```

`line326_reached` is the exact boolean of the guard at FLExProject.py:322-324
(`self.writeEnabled and not self._undoable`), evaluated against live state,
not assumed.

**[PASS]** -- CONFIRMED: `EndNonUndoableTask()` at line 326 is reachable
**only** in mode (b), `writeEnabled=True, undoable=False`. Mode (a) (the
4.4.0 default) and mode (c) (read-only) never reach it.

## P-2 -- depth table

`project.project.ActionHandlerAccessor.CurrentDepth`, read live at each
requested moment:

| Moment | CurrentDepth |
|---|---|
| After `OpenProject(undoable=False)` | 1 |
| After `OpenProject(undoable=True)` | 0 |
| Inside `with project.Transaction("probe"):`, undoable=False | 1 (unchanged) |
| Inside `with project.Transaction("probe"):`, undoable=True | 0 (unchanged) |
| Inside `with project.UndoableOperation("probe"):`, undoable=True | 1 |
| After `AbortSession()` returns True, undoable=False | 1 |
| Immediately after manual `EndNonUndoableTask()`, undoable=False | 0 |
| Reading `CurrentDepth` on a read-only project | 0 (no exception) |

**[PASS]** -- all eight readings taken from a live `ActionHandlerAccessor`.
Notably, `project.Transaction()` (the public, non-`_TransactionCM` method)
never touches `CurrentDepth` in either mode -- confirmed live, matching the
source's claim that it is a labelling-only wrapper with no LCM undo-task
interaction. `AbortSession()` reopens the envelope (depth back to 1), and a
manual `EndNonUndoableTask()` call drops depth to 0 with no error -- this is
exactly the state CloseProject()'s own mirror call needs, and exactly the
state P-3 forces one call early.

## P-3 -- the P0 reproduction, fully live, no mocks

Created 25 entries (`TEST_p3_000`..`TEST_p3_024`), then called
`project.project.MainCacheAccessor.EndNonUndoableTask()` manually once
(leaving CloseProject()'s own mirror with no task to end), then called
`project.CloseProject()`.

```
CloseProject() raised: InvalidOperationException: Cannot end task that has not been started.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.EndUndoTaskCommon(Boolean updateDateModified)
```

Because the raise happens at line 326, `CloseProject()` never reaches its
own `self.project.Dispose()` at line 334 -- confirmed by observation (the
cache had to be disposed manually in the test's `finally:` to release the
file lock before the reopen below could proceed).

Reopened the SAME `.fwdata` path read-only and counted `TEST_p3_` entries
by re-querying `project.LexEntry.GetAll()` / `GetLexemeForm()` -- **0
survivors out of 25**, matching the expected total-session-loss outcome.

**[PASS]** -- confirmed: the raise at line 326 skips the `usm.Save()` at
line 332, and the entire session (25/25 created entries) is lost.

## P-4 -- control run

Identical flow on a fresh sandbox copy, WITHOUT the manual `EndNonUndoableTask()`
call -- `CloseProject()` ran normally (`OK -> None`, no exception). Reopened
read-only and counted `TEST_p4_` entries: **25 survivors out of 25**.

**[PASS]** -- confirms the P-3 loss is caused by the End-before-Save
ordering plus the forced early End, not by anything about the sandbox
itself.

## P-5 -- the go/no-go for the P0 fix

On a fresh sandbox copy: created 25 `TEST_p5_` entries (`CurrentDepth` = 1,
envelope open), then called `project.SaveChanges()` (which calls
`usm.Save()` with no End mirror, exactly `CloseProject()`'s line 332 in
isolation) **while the envelope was still open**:

```
SaveChanges() while envelope still open: RAISED InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
```

`CurrentDepth` read immediately after this failed `SaveChanges()` call was
**0** -- i.e. `CheckReadyForCommit`'s failure path itself terminates the
open unit of work as a side effect of the check, before throwing. The
subsequent forced `EndNonUndoableTask()` call (per the required flow) then
failed too (`Cannot end task that has not been started.`), as did the
following `CloseProject()` call, for the same reason. Reopening read-only
and counting `TEST_p5_` entries: **0 survivors out of 25**.

**[PASS as a go/no-go finding] -- VERDICT: `usm.Save()` itself RAISES
(`InvalidOperationException: Commit at wrong place.`) while the
non-undoable session envelope is still open (`CurrentDepth` > 0). A plain
reorder of `SaveChanges()`/line 332 before the line 326 `EndNonUndoableTask()`
call is NOT a viable fix shape by itself** -- calling Save while the
envelope is open fails immediately and, per the observed depth drop, tears
down the envelope in the process. `SaveChanges()`'s own docstring claim
that "the session stays open" is disproved for this specific ordering: it
is true only when `Save()` is called with the envelope already closed (as
`CloseProject()` does today, lines 326 then 332), not before. The fix must
guard the line 326 `EndNonUndoableTask()` call itself (e.g. a
try/except-or-finally around it so a raise there cannot skip line 332), not
reorder Save ahead of End.

## P-6 -- the symptom and the file

In the P-3 run:

* `.fwdata` size before: 5158956 bytes. Size after the failed close (post
  manual dispose): 5158956 bytes. **Delta: 0** -- the file was NOT replaced
  or truncated on the sandbox.
* Sandbox directory listing before and after are identical:
  `['BackupSettings', 'ConfigurationSettings', 'SharedSettings',
  'Target.fwdata', 'WritingSystemStore']`. **No new sibling file
  (`.bak`, crash-recovery copy, etc.) appeared.**
* Searched the P-3 `CloseProject()` exception message and all captured
  stdout/stderr for the literal text `Commit at wrong place.`: **not
  found** in any of the three. The P-3 exception is
  `Cannot end task that has not been started.` (from
  `UndoStack.EndUndoTaskCommon`), a *different* liblcm failure than the
  `Commit at wrong place.` message (from `UndoStack.CheckReadyForCommit`,
  reproduced instead in P-5).

**[REFUTED, on this sandbox]** -- the owner's report that `.fwdata` was
replaced by a crash-recovery copy sized like the old `.bak` does not
reproduce here: on this Target sandbox, the failed `EndNonUndoableTask()` /
`CloseProject()` sequence leaves the on-disk `.fwdata` byte-for-byte
unchanged (data loss is entirely in-memory -- the 25 created entries never
reached disk at all, because `usm.Save()` never ran), and no recovery/backup
sibling file is produced by liblcm as part of this failure path. The
"`Commit at wrong place.`" symptom the owner reported is real and
reproduces (in P-5, under a related but distinct call sequence), but it did
not appear in the literal P-3 (mirror-fails-first) sequence -- worth naming
explicitly in the cycle-1 report rather than silently reconciling the two.

## Cleanup

Every project opened in every test was disposed (via `CloseProject()` where
it succeeded, or a manual `project.project.Dispose()` in a `finally:` where
`CloseProject()` raised before reaching its own `Dispose()` call). Every
test used a fresh `target_sandbox_path` tempdir copy of the Target
`.fwbackup`; all five tempdirs were deleted on fixture teardown. The real
Target project was never opened.

## Result

**[PASS]** -- all six probes (P-1..P-6) answered with values read back from
a live LCM cache (`run_mode: live`), 5/5 tests green. Headline finding for
the cycle-1 fix design: reordering `usm.Save()` ahead of
`EndNonUndoableTask()` is not viable -- `Save()` itself raises
(`Commit at wrong place.`) and collapses the envelope when called while
`CurrentDepth > 0`. The fix must wrap the existing line-326
`EndNonUndoableTask()` call so that a raise there cannot prevent line 332's
`usm.Save()` from running (try/finally-shaped guard), not reorder the two
calls.
