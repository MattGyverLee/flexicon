# STATUS -- 243-closeproject-save-guard (flexicon#243)

**Campaign:** `tier1-silent-data-loss`, queue item 1 of 4 (`active`).
**Last updated:** 2026-09-07, end of spurt 1 (cycle 1).
**Status:** `in_progress`. Spec+probe checkpoint COMPLETE. No code under
`flexicon/code/` has been modified yet.

---

## What landed in spurt 1

The campaign's entry condition for this item was "Checkpoint 1 = spec + live
probe." That is done, and the probe overturned the fix shape the issue prose
proposed.

- **Live probe** -- `tests/operations/test_issue243_closeproject_probe.py`
  (new), 5/5 passing, `run_mode: live`, `target_sandbox_path` fixture only.
  The real Target was never opened; no `scripts/restore_*.py` was run.
  Evidence: `evidence/live-cycle1-probe.md`.
- **`spec.md`** -- problem statement, live behaviour tables (P-1 mode matrix,
  P-2 depth table, P-3/P-4/P-5 survivor counts), the three surviving asks
  (P0/P1/P2), the withdrawn-and-out-of-scope section, 5 acceptance criteria,
  and frozen contract decisions **C1-C10**.
- **`tasks.md`** -- T1-T5 across three implementation checkpoints
  (**CP-A** = T1-T2, **CP-B** = T3-T4, **CP-C** = T5), sequenced so P1 lands
  before P0 per C6.
- **Reviews on file** -- `reviews/cycle1-programmer.md`,
  `reviews/cycle1-domain.md`, `reviews/cycle1-archivist.md`.

## The two findings that changed the plan

1. **The issue's proposed fix is wrong (C1).** Reordering `usm.Save()` ahead
   of `EndNonUndoableTask()` is not viable: `Save()` itself raises
   `InvalidOperationException: Commit at wrong place.` at `CurrentDepth > 0`,
   and its own failure path collapses the envelope (depth 1 -> 0) before
   propagating. Swapping the lines trades one guaranteed raise for another
   with no save either way. The fix GUARDS the existing End call at line 326
   so its exception cannot skip `Save()` at line 332; End-then-Save order is
   unchanged (C7).
2. **P1 is a prerequisite of P0, not a follow-on (C6).** The guard must ask
   the depth first and only call `EndNonUndoableTask()` when an envelope is
   actually open, so the depth-read surface has to exist first. `tasks.md`
   sequences T1-T2 before T3.

## Q1 ruled and CLOSED (2026-09-07, `/lex-lead`)

The probe could not reproduce two details of the owner's report. Both are now
decided; **no owner input is required and implementation is unblocked.**

- **`Commit at wrong place.` -- RECONCILED (C9).** P-5 and P-3 are not rival
  explanations; they are one chained sequence. A mid-session `SaveChanges()`
  under `undoable=False` reaches `usm.Save()` at depth 1, raises the owner's
  exact string, and collapses the envelope; the collapsed envelope then makes
  `CloseProject()`'s unguarded line-326 End raise, skipping line 332's
  `usm.Save()`, and the whole in-memory session is discarded. The frozen C6
  guard breaks that chain at its loss-bearing step. Decisively, the trigger is
  reachable from flexicon's own **shipped `SaveChanges()` docstring Example**
  (`FLExProject.py:563-588`), which is correct under `undoable=True` and a
  guaranteed raise under `undoable=False` -- the mode the owner switched to as
  their consumer-side remedy for the 4.4.0 default flip.
- **`.fwdata` file swap -- OUT OF SCOPE (C10).** `CloseProject()` has no path
  that renames, rotates, truncates or replaces `.fwdata`, so nothing in this
  feature's fix surface can cause or prevent a file swap. The probe's delta-0
  result is the *correct* consequence of `Save()` never running. Attributed to
  FieldWorks-side recovery/backup rotation and left unexplained by design.
  **P2 must not claim this fix prevents the file replacement.**

Two consequences were written back into the plan: T4's P-5 assertion was
raised from "does not compound the loss" to a **measured survivor count**
(intent 25/25, must be measured not assumed), and T5 picked up the
`SaveChanges()` **docstring** correction (prose only -- changing its behaviour
is out of scope).

## Still open

- **Q2** -- should the P0 fix also wrap the whole `CloseProject()` body in a
  `try/finally` so `Dispose()` always runs even when `Save()` raises? Decided
  at T3.
- **Q3** -- does the P1 surface warrant a `flexicon.CAPABILITIES` token?
  Decided at T1.
- **Q4** -- exact CHANGELOG placement/wording. `/lex-doc`'s call at T5.

## Next pickup

**CP-A / T1** -- add the private depth-read helper plus the public
`CurrentDepth` / `HasOpenSessionTask()` surface on `FLExProject` per C2-C5,
and live-verify it against every row of the frozen P-2 table plus the two new
closed/never-opened `FP_ProjectError` cases. This is the first task in the
feature that modifies `flexicon/code/`. Sandbox fixture only.

## Routed to the user (do not act on inside the loop)

One follow-up was spawned by the C9 ruling and deliberately NOT absorbed into
this feature, because `spec.md` section 4 binds it to the three surviving
asks: **`SaveChanges()` has no depth guard**, so under `undoable=False` it
turns a documented usage pattern into a liblcm exception that also destroys
the session envelope. Making it fail fast is a behaviour change and a fourth
ask. It is listed under "Awaiting user approval" in
`specs/tier1-silent-data-loss/QUEUE.md`.
