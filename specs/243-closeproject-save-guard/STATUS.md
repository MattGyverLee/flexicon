# STATUS -- 243-closeproject-save-guard (flexicon#243)

**Campaign:** `tier1-silent-data-loss`, queue item 1 of 4 (`active`).
**Last updated:** 2026-09-07, end of spurt 3 (cycle 3).
**Status:** `in_progress`. Spec+probe checkpoint COMPLETE (spurt 1).
**CP-A1 / T1 COMPLETE (spurt 2)** -- the P1 depth-read surface is landed and
live-verified. **CP-A2 / T2 is DROPPED on the merits (spurt 3, `spec.md` C12),
so CP-A is now CLOSED IN FULL with zero code diff from T2.** **CP-B (the P0
guard, T3-T4) is UNBLOCKED and is the next pickup**; CP-C (the CHANGELOG, T5)
follows. Not feature-complete.

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

## What landed in spurt 3 (cycle 3) -- CP-A2 / T2 DROPPED

**Zero lines of `flexicon/` changed this spurt, and that is the correct
outcome.** T2 was attempted exactly as specified and came back as a finding.
`/lex-lead` verified the claims independently rather than accepting the
report: `git diff f3a0f50 -- flexicon/` is empty, the offline suite is
`1290 passed` (the frozen pre-T1 baseline), the static source-grep test at
`tests/test_custom_field_create_refusal.py:54-60` exists as described, and
`test_transaction_rollback.py` collects 0 live tests.

**Ruling: T2 is DROPPED, not deferred.** Frozen as `spec.md` **C12**.

- All three prescribed delegations break the offline suite
  (`transaction.py:172` -> 9 failed, `undoable_operation.py:102` -> 2 failed,
  `System/CustomFieldOperations.py:306` -> 2 failed). All reverted in full.
- **The premise was wrong, so the task is wrong.** T1's helper is
  deliberately STRICT (raises `FP_ProjectError`; returns depth verbatim --
  C5); the three internal sites are deliberately LENIENT (coerce a non-`int`
  to `0` so a malformed double degrades to "treat as outermost"). One
  implementation cannot serve both contracts. Merging them is a conflation,
  not a de-duplication.
- **Both escape hatches rejected.** (1) An `isinstance(depth, int)` guard is
  behaviour-preserving in *production* but makes the doubles stop testing
  what they claim to -- and, decisively, the prescribed `except` wrapper
  would swallow the very `FP_ProjectError` the helper exists to raise and
  substitute `0`, which at `CustomFieldOperations.py:306` silently disables
  the issue-#21 corruption guard. Three duplicated depth reads are strictly
  better than that. (2) The static source-grep test is a deliberate pin on
  that corruption guard's implementation; loosening it to reach a "zero
  functional delta" refactor is net-negative, and satisfying it by parking
  the literals in a comment would be gaming it.
- **Adding `spec=` to the doubles is NOT owed as a follow-up.** T2 died on
  the merits, so its enabler has no purpose. Recorded in C12 as a
  non-blocking observation about three test files only -- not a task, not an
  open question, no issue filed.
- **Nothing downstream is affected.** C6's prerequisite was always the PUBLIC
  surface (T1); C5 had already made this consolidation optional.

### Second finding this spurt: a defect in `/lex-lead`'s own verification plan

T2's brief named three live suites **by filename**. Only one of them actually
verified anything: `test_transaction_rollback.py` carries zero
`requires_live_project` markers (0 collected, `20 deselected`) and
`test_custom_field_multistring_best_alt.py` env-skipped. The programmer
flagged this instead of silently substituting a file -- correct behaviour.

The live set for T3/T4 has been **re-derived from markers** and written into
`tasks.md`'s boilerplate section as binding: probe file (**6**) +
`test_undoable_mode_live.py` (**33**) + `test_target_live_smoke.py` (**3**),
with `test_transaction_rollback.py` run OFFLINE (20 tests) where its coverage
actually lives. Every future brief must paste the
`--collect-only -q -m requires_live_project` count into its evidence file. A
`no tests collected` result is a zero, never a pass.

---

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
  **STILL OPEN, decided at T3.** Untouched by spurts 2 and 3 -- T1's diff
  never entered `CloseProject()` and spurt 3 changed zero lines of
  `flexicon/`, so nothing about Q2 was silently decided.
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

C1-C10 (spurt 1), **C11** (spurt 2, the `HasOpenSessionTask()` ordering
ruling) and **C12** (spurt 3, T2 dropped -- the strict helper and the three
lenient internal sites keep separate depth reads permanently). Do not reopen
any of them; overturning C11 or C12 specifically requires citing it
explicitly.

## Next pickup

**CP-B / T3 (the P0 guard itself).** CP-B is UNBLOCKED: C6's prerequisite is
the PUBLIC depth-read surface and T1 shipped it; T2 is dropped (C12) and
nothing depends on it.

Implement the C1/C6 guard around `CloseProject()`'s line-326
`EndNonUndoableTask()` call, in `flexicon/code/FLExProject.py` only:

1. Check `self.HasOpenSessionTask()` BEFORE attempting the call; if no
   envelope is open, skip it and log at debug level rather than assuming the
   mode implies the envelope.
2. When an envelope IS open, still wrap the `EndNonUndoableTask()` call in
   try/except (or try/finally) so ANY raise from it -- not just the depth-0
   case the check already prevents -- cannot skip line 332's `usm.Save()`.

Do NOT reorder lines 326/332 (C7). Q1 is CLOSED (C9/C10) -- implement against
it. **Q2 is decided at T3**: if `try/finally`-wrapping the whole
`CloseProject()` body so `Dispose()` always runs turns out to be right, record
it as a dated note under `spec.md` Q2 -- do not just change the code and move
on.

**Live gate, re-derived from markers (binding -- see `tasks.md` boilerplate):**
`tests/operations/test_issue243_closeproject_probe.py` (6 live tests, grows
with T4) + `tests/operations/test_undoable_mode_live.py` (33) +
`tests/operations/test_target_live_smoke.py` (3), each with
`FLEXLIBS_REQUIRE_LIVE=1` and `-m requires_live_project`, `run_mode: live`,
`target_sandbox` fixture ONLY. Run `test_transaction_rollback.py` OFFLINE (20
tests) -- it has NO live markers. Plus the offline suite at `1290 passed`.
Paste the `--collect-only -q` count into the evidence file for each live file;
`no tests collected` is a zero, never a pass.

**Do not touch `SaveChanges()`** -- behaviour there is the user's open ruling.
**Do not re-attempt T2** (C12).

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
