# Cycle 1 -- programmer probe findings: issue #243 CloseProject() save-guard

Live evidence: `specs/243-closeproject-save-guard/evidence/live-cycle1-probe.md`
(`run_mode: live`, 5/5 probe tests passed, Target sandbox only, real Target
untouched). Probe-only checkpoint; nothing under `flexicon/code/` changed.

## P-1 mode matrix

| Mode | writeEnabled | _undoable | line 326 reached |
|---|---|---|---|
| (a) default (4.4.0), undoable=True | True | True | **False** |
| (b) undoable=False | True | False | **True** |
| (c) read-only | False | False | False |

**Confirmed:** the `EndNonUndoableTask()` mirror at line 326 is reachable
**only** in mode (b). The 4.4.0 default (undoable=True) and read-only mode
never reach it -- this bug requires an explicit `undoable=False` opt-in.

## P-2 depth table

| Moment | CurrentDepth |
|---|---|
| OpenProject(undoable=False) | 1 |
| OpenProject(undoable=True) | 0 |
| `Transaction()` block, undoable=False | 1 (unchanged) |
| `Transaction()` block, undoable=True | 0 (unchanged) |
| `UndoableOperation()` block, undoable=True | 1 |
| after `AbortSession()`==True, undoable=False | 1 |
| after manual `EndNonUndoableTask()`, undoable=False | 0 |
| `CurrentDepth` on read-only project | 0, no exception |

`project.Transaction()` is confirmed live to never touch `CurrentDepth` in
either mode (pure labelling wrapper). `AbortSession()` correctly reopens the
envelope. This table is clean input for a P1 API design: any depth-based
guard around line 326 can safely check `CurrentDepth > 0` before calling
`EndNonUndoableTask()`, since normal operation always has depth 1 at that
point and depth 0 unambiguously means "already ended."

## P-3 / P-4 / P-5 counts

| Probe | Setup | Forced failure | CloseProject() | Reopen count |
|---|---|---|---|---|
| P-3 | 25 entries | manual `EndNonUndoableTask()` before close | raised `Cannot end task that has not been started.` | **0/25** |
| P-4 (control) | 25 entries | none | succeeded | **25/25** |
| P-5 | 25 entries | `SaveChanges()` called at depth=1, then forced End | `SaveChanges()` raised `Commit at wrong place.`; depth dropped to 0 as a side effect; forced End and CloseProject() both then raised too | **0/25** |

P-3 vs P-4 isolates the ordering as the cause of loss, not the sandbox. P-5
is the critical result: `usm.Save()` (via `SaveChanges()`) does **not**
tolerate being called while the envelope is still open -- it raises
immediately and its own failure path collapses the envelope (depth 1 -> 0)
before propagating.

## Verdict on P-5 (fix shape)

**Reordering `Save()` ahead of `EndNonUndoableTask()` is NOT a viable fix
shape.** `Save()` itself raises `InvalidOperationException: Commit at wrong
place.` when called at `CurrentDepth > 0`, and the failure also tears down
the envelope as a side effect -- so simply swapping lines 326/332 would
trade one guaranteed-raise for another guaranteed-raise, with no save
occurring either way. The fix must instead **guard the existing
`EndNonUndoableTask()` call at line 326** (a try/except or try/finally
shape) so that if it raises, execution still reaches `usm.Save()` at line
332 -- End-then-Save stays the correct order, but End's exception must not
skip Save.

## P-6 symptom and file

`.fwdata` size was unchanged before/after the P-3 failed close (delta 0,
byte-for-byte), and no new sibling file (`.bak`, crash-recovery copy)
appeared in the sandbox directory. **The owner's "file replaced by a
smaller recovery copy" report does not reproduce on this sandbox** -- here
the loss is purely in-memory (the 25 entries never reached disk because
`Save()` never ran), not a disk-level file swap. Also worth flagging: the
literal `Commit at wrong place.` text the owner cited did **not** appear in
the P-3 (mirror-fails-first) exception or captured output -- that message
is specific to the `CheckReadyForCommit` path, which P-3's sequence never
reaches (its exception is `Cannot end task that has not been started.`
instead, from `EndUndoTaskCommon`). The `Commit at wrong place.` message
reproduces in P-5's distinct sequence (calling `Save()`/`SaveChanges()`
while depth > 0). The owner's real-world crash likely involved a `Save()`
call reached at the wrong depth (matching P-5), not literally the P-3
double-End sequence -- worth reconciling with the owner's original repro
steps before finalizing the P1 fix design.
