# Cycle 5 -- Programmer report: T6 no-op-save mechanism probe

Task: `tasks.md` T6 only. Extended
`tests/operations/test_issue243_closeproject_probe.py` in place with P-7,
P-8, P-9 (probe file 6 -> 9 live tests), and added the missing
`close_exc_msg` assertion to `test_p5_save_before_forced_end`, closing CP-B
defect 2. No `flexicon/` file touched.

## Headline: mechanism (ii) is CONFIRMED, not merely favoured

**P-7** re-read the 25 `TEST_p7_` entries from the STILL-OPEN project
immediately after `SaveChanges()` raised at `CurrentDepth == 1`, before
`CloseProject()` was ever called: **0/25 in memory.** The change set was
already gone one full step before `CloseProject()`'s own code even runs.
This is the single most consequential fact in this cycle: **it settles
#243's ceiling.** No change on the `CloseProject()` side -- not T3's guard,
not any future guard in that method -- could ever recover the owner's real
P-5 -> P-3 sequence's data, because it never survives as far as
`CloseProject()`. Only the still-queued `SaveChanges()` fourth ask could fix
that path. T3's independent fix for the intact-change-set P-3 scenario
(0/25 -> 25/25) is untouched by this and stands as shipped.

**P-8** rules out mechanism (i): a fresh `BeginNonUndoableTask()`/
`EndNonUndoableTask()` pair opened AFTER the failure committed its own new
entry cleanly (1/1), in the same process. The `UnitOfWorkService` is not
globally poisoned; only the change set that was in flight when
`CheckReadyForCommit` failed is unrecoverable.

Mechanism (iii) is not separately distinguishable from (ii) by anything
measured here -- both describe the same loss point and the same scope
conclusion, so this is left unresolved by design (documented in the
evidence file).

## P-9 detector: usable, but not as a standalone post-Save() check

The live `IUndoStackManager` (concrete type `UnitOfWorkService`) exposes
`HasUnsavedChanges` (bool property; member list recorded verbatim in
evidence). Measured immediately after `usm.Save()`, it reads `False` in
BOTH the real-save case (25/25 persisted) and the no-op case (0/25
persisted) -- **indistinguishable**. Measured immediately BEFORE the save,
it reads `True` (real) vs `False` (no-op) -- **distinguishable**, and
consistent with P-7's finding, but only observed under mechanism (ii)/(iii)
since (i) was ruled out here, so it is not proven mechanism-independent.
**T7 recommendation (prose only, not implemented):** the
Phase-1-envelope-missing heuristic (already available from T1's
`HasOpenSessionTask()`) remains necessary as T7's primary detector; a
pre-Save() `HasUnsavedChanges` read inside that anomalous branch could
usefully sharpen the error message ("...and there is nothing pending to
save") but should not replace the envelope-missing check or be presented as
proving anything beyond what was measured.

## Verification

`git diff --stat -- flexicon/` is empty. Probe file 9/9 live
(`run_mode: live`), `test_undoable_mode_live.py` 33/33,
`test_target_live_smoke.py` 3/3, all live. Offline suite unchanged at 1290
passed (deselected 470 -> 473, exactly the +3 new live tests). Full detail,
verbatim console lines (including CP-B defect 2's `[PROBE][P5]` transcript)
and reflection output: `evidence/live-t6-noop-save-mechanism.md`.

**PASS.**
