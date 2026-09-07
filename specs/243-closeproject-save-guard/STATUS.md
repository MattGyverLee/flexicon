# STATUS -- 243-closeproject-save-guard (flexicon#243)

**Campaign:** `tier1-silent-data-loss`, queue item 1 of 4 (`active`).
**Last updated:** 2026-09-07, end of spurt 2 (cycle 2).
**Status:** `in_progress`. Spec+probe checkpoint COMPLETE (spurt 1).
**CP-A1 / T1 COMPLETE (spurt 2)** -- the P1 depth-read surface is landed and
live-verified. CP-A is SPLIT: **CP-A2 / T2 is the next pickup.** CP-B (the P0
guard, T3-T4) and CP-C (the CHANGELOG, T5) remain. Not feature-complete.

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

---

## What landed in spurt 2 (cycle 2) -- CP-A1 / T1

**T1 is the first task in this feature that modified `flexicon/code/`.**
The P1 depth-read surface is now shipped in
`flexicon/code/FLExProject.py`, inserted between `CloseProject()` and the
`Cache` property:

- `_ReadActionHandlerDepth()` -- private helper. Raises `FP_ProjectError`
  when `not hasattr(self, "project")`; otherwise returns
  `self.project.ActionHandlerAccessor.CurrentDepth` verbatim.
- `CurrentDepth` -- implemented as a **property** (implementer's choice per
  T1, matching the `Cache` property precedent: no-argument, no-side-effect,
  discoverable read of raw LCM state).
- `HasOpenSessionTask()` -- method. Reads depth first, then returns `False`
  under `undoable=True`, else `depth > 0`. See C11 below.

### Verification (checked by `/lex-lead`, not taken on the report's word)

- **Live:** extended probe 6/6 passing (5 cycle-1 probes unchanged + new
  `test_p2_public_surface_matches_depth_table`), `tests/live_status.json`
  `"run_mode": "live"`, `target_sandbox_path` fixture only -- real Target
  never opened, no `scripts/restore_*.py` run.
  Evidence: `evidence/live-t1-depth-read-surface.md`.
- **Contract conformance:** all 8 frozen P-2 rows agree exactly via the new
  public surface, including `HasOpenSessionTask() == False` at depth 1 inside
  `UndoableOperation()` (C3) and read-only returning `0`/`False` without
  raising (C4). Both new C4 raise cases -- after a successful
  `CloseProject()`, and on a never-opened `FLExProject()` -- raise
  `FP_ProjectError`.
- **Scope fences, independently confirmed:** `git diff --stat flexicon/code/`
  = **120 insertions, 0 deletions, one file**. Purely additive, so
  `CloseProject()` (T3) and `SaveChanges()` (the user-approval item) are
  *provably* untouched. `flexicon/__init__.py` and
  `tests/write_path_transactions/test_capabilities.py` are not in the
  changed-file list, so Q3's NO ruling held.
- **C5 holds:** the helper is `if not hasattr(...): raise FP_ProjectError(...)`
  then a bare passthrough -- no `except: return 0`, no `getattr(..., 0)`, no
  coercion. The lenient fallback stayed out of the public surface.
- **No regression:** offline suite 1290 passed, 470 deselected -- identical
  to the pre-T1 baseline.

### The one deviation, reviewed and CONFIRMED -> new contract decision C11

The cycle-2 dispatch brief said `HasOpenSessionTask()` should return `False`
"WITHOUT consulting depth" under `undoable=True`. The implementation reads
depth FIRST, then short-circuits. **That deviation was raised explicitly
rather than accepted silently, and `/lex-lead` ruled it CORRECT -- the brief
wording was wrong and is now superseded by spec.md C11.** Two independent
reasons:

1. C4 requires closed/never-opened to raise in BOTH members with no mode
   carve-out. Short-circuiting first would make a closed `undoable=True`
   project answer `False` instead of raising -- the exact silent-answer
   ambiguity P1 exists to remove.
2. `FLExProject` has no `__init__`, and `OpenProject()` assigns
   `self.project` (line ~263) BEFORE `self._undoable` (line 271). On a
   never-opened instance, testing `self._undoable` first raises a bare
   `AttributeError`, not the documented `FP_ProjectError`.

C3 is NOT weakened: `depth` is read for its raise-or-not effect only and
discarded unread on the Phase 2 branch, so the ANSWER is still never
depth-derived under `undoable=True`. **C11 is binding -- do not "fix" this
back to the literal brief wording.**

### Why the spurt stopped here rather than continuing into T2

T1 is a clean stopping point: one file, purely additive, live-verified, zero
regression, nothing half-written. T2 (the C5 internal-call-site
consolidation) was deliberately gated into its own sub-checkpoint **CP-A2**
because it touches three *different* files (`transaction.py`,
`undoable_operation.py`, `System/CustomFieldOperations.py`) and is a
behaviour-preserving refactor whose whole claim is "zero functional delta" --
that claim is only auditable in a diff that contains nothing else.

## The two findings that changed the plan (spurt 1)

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
  `try/finally` so `Dispose()` always runs even when `Save()` raises?
  **STILL OPEN, decided at T3.** Untouched by spurt 2 -- T1's diff never
  entered `CloseProject()`, so nothing about Q2 was silently decided.
- **Q4** -- exact CHANGELOG placement/wording. `/lex-doc`'s call at T5.
  **STILL OPEN.**

### Closed questions -- do not relitigate after a context reset

- **Q1** -- CLOSED spurt 1 (spec.md C9/C10). The owner's incident is a
  P-5 -> P-3 chain; no owner repro steps needed.
- **Q3** -- CLOSED spurt 2, 2026-09-07: **NO capability token.** Recorded in
  `spec.md` under Q3 (not merely in a dispatch rationale) and in `tasks.md`'s
  header, so it survives a context reset. `flexicon/__init__.py` and
  `tests/write_path_transactions/test_capabilities.py` are out of scope for
  every remaining task. The single reopening condition is a real consumer
  that cannot use `hasattr(project, "HasOpenSessionTask")` -- and that would
  be a NEW ask routed to QUEUE.md, not absorbed here.

### Contract decisions now frozen

C1-C10 (spurt 1) plus **C11** (spurt 2, the `HasOpenSessionTask()` ordering
ruling above). Do not reopen any of them; overturning C11 specifically
requires citing it explicitly.

## Next pickup

**CP-A2 / T2 (alone).** Point the three existing lenient internal depth reads
(`transaction.py:172`, `undoable_operation.py:102`,
`System/CustomFieldOperations.py:306`) at T1's shared
`_ReadActionHandlerDepth()` helper, **keeping each call site's own
`try/except` / `getattr(..., 0)` fallback WRAPPED AROUND the helper call**
(C5: the lenient fallback stays out of the public surface, not out of
existence). Behaviour-preserving -- zero functional delta expected.

T1's report confirms the helper's signature permits this shape without
modification: it takes only `self` and either raises or returns the raw int,
so each call site can wrap `project._ReadActionHandlerDepth()` exactly as it
wraps its current read.

Live-verify the three existing suites at UNCHANGED pass counts, one file per
invocation, `FLEXLIBS_REQUIRE_LIVE=1` with `-m requires_live_project`:
`tests/operations/test_transaction_rollback.py`,
`tests/operations/test_custom_field_multistring_best_alt.py`,
`tests/operations/test_undoable_mode_live.py`.

Sandbox fixture only. Evidence file
`evidence/live-t2-internal-callsite-dedup.md` recording all three commands,
`run_mode`, and before/after pass counts.
**Do not start T3** -- CP-B is gated behind CP-A2.

## Routed to the user (do not act on inside the loop)

**Still awaiting the user's ruling as of end of spurt 2 -- nothing in spurt 2
acted on it, and `SaveChanges()` was not modified (proved by the 0-deletion,
one-file T1 diff).** One follow-up was spawned by the C9 ruling and
deliberately NOT absorbed into
this feature, because `spec.md` section 4 binds it to the three surviving
asks: **`SaveChanges()` has no depth guard**, so under `undoable=False` it
turns a documented usage pattern into a liblcm exception that also destroys
the session envelope. Making it fail fast is a behaviour change and a fourth
ask. It is listed under "Awaiting user approval" in
`specs/tier1-silent-data-loss/QUEUE.md`.
