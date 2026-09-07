# STATUS -- 243-closeproject-save-guard (flexicon#243)

**Campaign:** `tier1-silent-data-loss`, queue item 1 of 4 (`active`).
**Last updated:** 2026-09-07, end of spurt 5 (cycle 5).
**Status:** `needs_human`. **STOPPED ON A BLOCKER, not on a failure.**
**THE RALPH LOOP IS CANCELLED** -- the Stop hook will no longer re-feed
anything. Nothing in this feature resumes automatically. See
**"How a human restarts this"** at the bottom.

> ## THE ONE FACT THIS FEATURE TURNS ON (C17, measured at T6)
>
> **The owner's filed incident cannot be fixed by anything in #243's scope.**
> T6/P-7 measured the 25 entries as already gone from the **still-open**
> project immediately after `SaveChanges()` raised -- **before
> `CloseProject()` is ever entered.** So no `CloseProject()`-side change --
> not T3's shipped guard, not T7, not any future guard there -- can ever
> recover that data. **Only the still-unruled `SaveChanges()` depth guard
> can.**
>
> **And, unqualified: T3 IS a real, shipped, live-verified fix for the P-3
> path** (intact change set + stray/forced `End`): 0/25 -> 25/25. C17 does
> not weaken that.
>
> **Say both halves. Either alone is a misrepresentation.**

Spec+probe (spurt 1), **CP-A1/T1** (spurt 2) and **CP-A closed in full** with
T2 dropped (spurt 3) are done. **CP-B (T3-T4, the P0 guard) REACHED AND
PASSED (spurt 4)** -- the guard is landed, live-verified, and P-3 is fixed
0/25 -> 25/25 with no raise. But the same cycle measured **P-5 at 0/25**, and
ruling on that produced two new contract decisions and one blocker:

- **C13** -- what the P-5 measurement does and does NOT establish. The
  "guard skipped an End that should have run" hypothesis is DISPROVED by
  measurement; the asserted `UnitOfWorkService` internals mechanism is NOT
  established and must not be cited as settled.
- **C14** -- T3's quiet path is a **new silent-loss surface**: for the
  owner's real P-5 -> P-3 chain, `CloseProject()` now returns normally while
  persisting nothing, where before it raised. Fixing that is in scope for
  #243 (new task T7).
- **C15** -- Q2(a) RESOLVED (forced by C14): `Dispose()` moves into a
  `try/finally`.

**Not feature-complete, and it cannot become so inside the loop.** Honestly
closing #243 requires the user's ruling on the `SaveChanges()` depth guard --
the campaign's fourth ask, unruled for three spurts and now BLOCKING. New
task order: **T6 (probe, ruling-independent) -> T7 (the C14 remedy, blocked)
-> T5 (CHANGELOG, last)**.

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

## What landed in spurt 4 (cycle 4) -- CP-B / T3 + T4: PASSED, plus three rulings

Crew: `lex-programmer` alone (T3 and T4 dispatched together -- T4 is T3's
regression proof and the CP-B checkpoint line requires both green).

### T3 + T4 as delivered -- ACCEPTED

`flexicon/code/FLExProject.py` `CloseProject()`, +52 lines: the Phase-1
`EndNonUndoableTask()` mirror is now (1) conditional on
`self.HasOpenSessionTask()` and (2) wrapped in `try/except` when the check
says an envelope IS open, so no raise there can skip `usm.Save()`. Lines
326/332 order unchanged (C7).

**Verified independently by `/lex-lead`, not taken on the report's word:**

- **P-3: 0/25 -> 25/25, no raise.** The loss mechanism C9 names is fixed.
  `.fwdata` grew by 20,625 bytes and a `Target.bak` sibling appeared --
  correct now that `usm.Save()` actually persists.
- **P-4 control: 25/25 unchanged.** No regression on the happy path.
- Live gate green with `run_mode: live`: probe **6/6**,
  `test_undoable_mode_live.py` **33/33**, `test_target_live_smoke.py`
  **3/3**; `test_transaction_rollback.py` **20/20 offline**; full offline
  suite **1290 passed**, unchanged. All four marker counts derived with
  `--collect-only` per the spurt-3 rule and pasted into the evidence file.
- Guard read directly in source: it consumes T1's P1 surface as C6 requires
  (a real `HasOpenSessionTask()` check, not a bare `try/except`), so
  acceptance criterion 4 holds.
- Scope fence honoured: `SaveChanges()` provably unmodified, no scope-fence
  file touched. **Minor record correction:** the spurt's diff also contains
  `.claude/ralph-loop.local.md` (+8/-76), which is the ralph-loop plugin
  overwriting its own stale scratch state from an unrelated old loop. Not
  `flexicon/`, not a spec artifact, harmless -- noted so the file list is
  accurate rather than tidy.

**Acceptance criteria 1, 2, 3 and 4 are satisfied. CP-B PASSES.**

### The P-5 measurement, and the three rulings it forced

P-5 (the owner's actual sequence: mid-session `SaveChanges()` at
`CurrentDepth=1`, then the collapsed envelope, then close) measured **0/25,
not the intended 25/25** -- the branch T4 named in advance, correctly
reported rather than absorbed into scope.

**Ruling 1 -- the guard is correct; do NOT rework T3.** Frozen as **C13**.
The rival hypothesis ("the guard skipped an `End` that should have run", which
would implicate the fix SHAPE) is **disproved by measurement in the same
run**: the probe force-calls `EndNonUndoableTask()` manually before
`CloseProject()` and that forced call still raises `Cannot end task that has
not been started.` The envelope was genuinely gone -- an `End` could not have
succeeded whether the guard attempted it or skipped it. C1/C6/C7 stand.

**Ruling 2 -- the internals mechanism is NOT established and is not frozen.**
"The `UnitOfWorkService` cannot commit after a failed `CheckReadyForCommit`"
is a claim about liblcm internals inferred from one black-box survivor count.
C13 records three rival mechanisms that produce identical observations, and
one of them -- **`SaveChanges()`'s failure path discarded the change set** --
would mean the data is already gone before `CloseProject()` is entered, so no
`CloseProject()`-side change could EVER reach 25/25. That is decisive for
#243's ceiling, so it goes to a probe (**T6**, P-7/P-8/P-9) rather than into
the contract. What IS frozen: `usm.Save()` returned successfully having
persisted nothing (a sound inference -- the `usm.Save()` call is bare, so a
raise would have propagated).

**Ruling 3 -- YES, we created a new silent-loss surface.** Frozen as **C14**,
and this is the most consequential finding of the spurt:

| | data | signal on the close path |
|---|---|---|
| before T3 | 0/25 lost | `CloseProject()` **RAISED** |
| after T3 | 0/25 lost | `CloseProject()` **returns normally**; one `debug` line |

Identical loss; the only close-path signal removed. The filed complaint was
verbatim *"the only symptom logged was a single `[WARN] Commit at wrong
place.`"* -- post-T3 the close path is quieter than that. **The instruction
was wrong, not the implementation:** `tasks.md` T3 said "log at debug level",
and in Phase 1 a `False` from `HasOpenSessionTask()` is anomalous by
construction (the envelope holds depth 1 all session per the P-2 table), so
that branch means we are standing inside the owner's incident. Logging it at
the quietest available level and returning normally is the defect. Same class
as C11 -- a `/lex-lead` brief-wording error, not a programmer deviation.
Remedy is **T7**: log at ERROR, always attempt `usm.Save()`, then RAISE when
the save cannot be trusted, with `Dispose()` in a `finally` (**C15**).
**T7 restores loudness, not data.**

### Second CP-B defect found in review

`test_p5_save_before_forced_end` captures `close_exc_msg` and **never
asserts it** (P-3 asserts `close_exc_msg is None` at line 434), and the
evidence file transcribes pass-counts rather than the `[PROBE][P5]` console
lines from its `-s` run. That "did not raise" claim is load-bearing for C13
fact 3 -- it is the whole difference between a silent no-op and a loud raise
-- so T6/P-9 must pin it with an assertion and a verbatim quote. Ruled on the
likely case; named the one un-pinned fact rather than building on it quietly.

### Q2 disposition -- the cycle-4 note was MISFILED, and has been moved

Cycle 4 filed the P-5 finding as note (b) under Q2. Q2 asks what happens if
`usm.Save()` **raises** after the guard runs; the P-5 finding is the exact
complement -- it does **not** raise and silently persists nothing. Opposite
branch, different remedy. So: (a) the original try/finally-around-`Dispose()`
question is **RESOLVED as C15** (forced by C14, after being legitimately
untouched by T3), and (b) is **moved to a new Q5**, whose only genuinely open
part is the detector question T6/P-9 answers.

---

## What landed in spurt 5 (cycle 5) -- T6, and four rulings

**Run as a ONE-SHOT on the user's explicit greenlight of T6 and T6 only, not
inside the loop.** The user greenlit the pre-authorised probe after spurt 4's
`needs_human` handoff; the main session ran it as a single dispatch rather
than restarting the ralph loop, precisely so nothing could drift into T7 or
T5. Crew: `lex-programmer` alone.
Report: `reviews/cycle5-programmer.md`.
Evidence: `evidence/live-t6-noop-save-mechanism.md`.

### T6 as delivered -- ACCEPTED

- **`git diff --stat -- flexicon/` is EMPTY** (re-verified by `/lex-lead`):
  **zero behaviour change**, so T6 stayed ruling-independent exactly as it
  was designed and pre-authorised to be. Changed files are the probe test
  file plus the two new `specs/` documents.
- Probe file **6 -> 9** live tests (9 `def test_` functions confirmed by
  direct grep), all green, `run_mode: live`, `target_sandbox_path` only;
  `test_undoable_mode_live.py` 33/33; `test_target_live_smoke.py` 3/3.
- Offline suite **1290 passed**, deselected **470 -> 473** -- exactly the +3
  new live tests, not a regression.
- **CP-B defect 2 CLOSED.** `test_p5_save_before_forced_end` now asserts
  `close_exc_msg is None` (probe line 575, confirmed in source), and the
  `[PROBE][P5]` console lines are quoted verbatim in the evidence file. C13
  fact 3 is now pinned by a measurement instead of prose.

### Ruling 1 -- C16: the mechanism question is ANSWERED, and its limit is recorded honestly

**(ii) CONFIRMED** -- P-7 read **0/25** from the still-open project after
`SaveChanges()` raised, before `CloseProject()` was entered.
**(i) RULED OUT** -- P-8's fresh post-failure envelope committed **1/1**, so
the `UnitOfWorkService` is not globally poisoned (which also *contradicts*
the cycle-4 report's asserted "cannot commit after a failed
`CheckReadyForCommit`" wording).
**(iii) NOT separately distinguishable from (ii)** by anything measured --
both name the same loss point and the same scope conclusion, so it is
**left unresolved by design**, not guessed at. The T6 report volunteered
that limit itself rather than tidying it into certainty; that is the correct
outcome and it is recorded that way. Splitting (ii) from (iii) would need
instrumentation inside liblcm -- outside this project's reach, and a new
issue against liblcm if anyone ever wants it (same disposition as C10).

### Ruling 2 -- C17: #243's CEILING, stated as a contract item

The consequence of C16 is that **the change set never survives as far as
`CloseProject()`**, so **no `CloseProject()`-side change can ever recover
the owner's real P-5 -> P-3 sequence.** T7 included. See the banner at the
top of this file -- it is duplicated there on purpose so a context reset
cannot miss it. C14 said "loudness, not data" from an inference; C16 is now
the **measurement** that proves it. T3's independent P-3 fix stands as
shipped.

### Ruling 3 -- C18: T7's detector, re-scoped so it cannot be over-claimed

`HasUnsavedChanges` exists on the live `UnitOfWorkService`, but read
**after** `usm.Save()` it is `False` in both the real-save (25/25) and no-op
(0/25) cases -- **indistinguishable**, so **C14 point 3's preference for a
direct post-save read is void.** The programmer's prose-only recommendation
(keep the envelope-missing heuristic as primary; use a pre-`Save()` read only
to sharpen the message) is **ACCEPTED**, with two additions `/lex-lead` took
from the evidence rather than the report:

1. The pre-`Save()` read is **not independent information** -- P-9 read
   `True` only *after a successful `End`*, so it is a proxy for "did an End
   just succeed", which `CloseProject()` already knows first-hand from its
   own End attempt. Diagnostic only; it must not gate the raise.
2. **The suggested wording is REJECTED.** `HasUnsavedChanges == False` must
   NOT be worded as "there is nothing pending to save" -- **proven
   false-negative in this very run**: in the no-op shape it read `False`
   before the trigger `SaveChanges()`, while all 25 entries still existed in
   memory. It means "a completed-but-unsaved unit of work is registered",
   not "dirty data exists". Telling a user nothing was pending at the moment
   they lost 25 objects is the same class of overclaim C10 and C14 exist to
   prevent.

### Ruling 4 -- C19: T5 is SPLIT; deferring all of it was not neutral

`CHANGELOG.md` has a live `[Unreleased]` section and **T3 is already on
`main` inside that window with no entry at all** -- so a version cut today
would ship an undocumented behaviour change to a public method, C14's
observability regression included. **T5a** (a minimal `[Unreleased]` stub
noting T3 only, scoped to C17's two halves) is **ruling-independent and
RECOMMENDED**: it describes shipped behaviour, takes no position on the
fourth ask, discloses nothing public issue #243 does not already say, and
its churn cost is **zero** because it can be edited before any version cut.
**T5b** (the prominent release note + the `SaveChanges()` docstring
correction + Q4) **stays gated** behind T7 and the ruling. T5a is *offered*
as a second pre-authorised unit -- the user's to greenlight, as T6 was.

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

- **Q2** -- **RESOLVED spurt 4 as C15**: yes, `Dispose()` moves into a
  `try/finally`. It was legitimately still open after T3 (T3's scope never
  forced an answer, and nothing about it was silently decided in spurts
  1-3); C14's new raise is what forces it, since a raise emitted after
  `usm.Save()` must not leak the LCM handle.
- **Q5** -- **NEW spurt 4; DETECTOR HALF CLOSED spurt 5.** `usm.Save()`
  returns successfully having persisted nothing: how must `CloseProject()`
  detect and report that? Facts frozen (C13), severity and remedy ruled
  (C14), mechanism now ANSWERED (**C16**) with its scope consequence frozen
  (**C17**), and the DETECTOR **RESOLVED as C18** -- the post-`Save()`
  `HasUnsavedChanges` read is indistinguishable and unusable; the
  envelope-missing anomaly is primary; the pre-`Save()` read is
  diagnostic-only and must not be worded as "nothing pending to save".
  **What remains open under Q5 is ONLY the user's coupled ruling.**
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
ruling), **C12** (spurt 3, T2 dropped -- the strict helper and the three
lenient internal sites keep separate depth reads permanently), and
**C13/C14/C15** (spurt 4: what the P-5 measurement does and does not
establish; the new silent-loss surface and its T7 remedy; Q2(a) resolved),
and **C16/C17/C18/C19** (spurt 5: the mechanism verdict with (iii) left
undetermined by design; **#243's CEILING**; T7's re-scoped detector; the T5
split). Do not reopen any of them; overturning C11-C19 specifically requires
citing it explicitly. Note that **C18 supersedes C14 point 3** and **C16/C17
answer C13's "NOT frozen" paragraph** -- read those originals as history.

## Next pickup -- BLOCKED, and the loop is CANCELLED. Read the blocker first.

**Item 1 is `needs_human`.** T6 -- the one pre-authorised exception -- is now
DONE, so **nothing in this feature is startable without the user.**

### The blocker, RESTATED on T6's sharpened facts

**One decision, two coupled parts:** does `SaveChanges()` get a
`CurrentDepth` guard so it fails fast instead of calling `usm.Save()` at
depth > 0 -- and, given that answer, should `CloseProject()` raise when it
detects a save it cannot trust (C14/T7)?

**What T6 changed about this decision.** Before T6, the `SaveChanges()` guard
read as an extra ask that "would also help". **After C16/C17 it is measured
to be the ONLY thing that can fix the incident #243 was filed about** -- the
data is gone before `CloseProject()` is entered, so #243's own three asks
cannot fix it at any price. **So the user is not deciding whether to approve
an improvement; they are deciding whether flexicon fixes #243's incident at
all, or ships #243 documenting it as unfixed.**

The coupling itself is unchanged, but the decline branch is now heavier:

- **Approve the `SaveChanges()` guard** -> the envelope is never collapsed,
  the change set is never discarded, the P-5 chain never forms, the owner's
  sequence can reach 25/25, and T7's raise is near-unreachable defensive
  code (still worth having; low-stakes wording).
- **Decline it** -> **permanently unfixable, by measurement**. T7's ERROR +
  raise becomes the entire remedy the owner ever gets, so its severity and
  wording matter a great deal.

**One observation for the decision, not a new ask.** C16 places the loss
*inside* `SaveChanges()`, so even T7's raise reports it **late**. If the
"fail fast / prevent" shape is declined, the honest maximum available is
"loud at close, already lost at `SaveChanges()`". Whether that same fourth
ask should have a *minimum* shape (report loudly at the point of loss) is
part of the ruling about that one method. It is **not** a fifth ask and
nothing may implement, prototype or plan it. `SaveChanges()` stays
untouchable.

### How a human restarts this

The ralph loop is **cancelled** -- the Stop hook is gone
(`.claude/ralph-loop.local.md` is deleted in the working tree) and will not
re-feed a standing prompt. Nothing happens until a human acts. In order:

1. **Rule on the blocker above** (both parts, together). That is the only
   thing standing between this feature and completion.
2. **Optionally greenlight T5a first** (C19) -- it is ruling-independent,
   docs-only, zero churn cost, and it closes the "T3 shipped undocumented"
   gap immediately. It does **not** unblock T7 or T5b.
3. **Then, and only then, restart the campaign loop** with the standing
   prompt from `lex-lead.md`'s "Spurt Mode & the Ralph Handoff Loop"
   section, e.g.:
   `/ralph-loop "Resume the LEX crew on the active feature. Read specs/tier1-silent-data-loss/QUEUE.md and specs/243-closeproject-save-guard/.crew-handoff.json, then invoke /lex-lead in spurt mode. ..." --completion-promise "TIER1 COMPLETE"`
   The campaign promise is `TIER1 COMPLETE`, **not** `FEATURE COMPLETE` --
   a per-feature completion must not exit the campaign loop.
4. **Entry point after the ruling:** T7, then T5b. Do **not** start T5b
   first. Do not re-run T6 (done, evidence on file). Do not re-attempt T2
   (C12).

**Why this is a real blocker and not caution** (any one of these suffices):

1. **Two coupled public-API decisions, both the user's.** T7 makes
   `CloseProject()` raise where it currently returns cleanly -- a behaviour
   change to a shipped public method, in the same failure path as the unruled
   fourth ask.
2. **Closing #243 now would be a false completion by the campaign's own
   standard.** C9 is our ruling that the owner's incident is the P-5 -> P-3
   chain; the campaign is named `tier1-silent-data-loss`. Stamping item 1
   done while the owner's own measured sequence loses 25/25 silently would
   report as fixed the exact thing this campaign exists to catch. T5's
   release note would have to either claim a fix that does not hold for the
   filed incident, or publicly document that it is unfixed -- and the latter
   commits the project to a position on the fourth ask.
3. **The decision has become blocking, where before it was merely queued.**
   Spurts 1-3 produced spec, T1 and a T2 drop, none of which touched it. As
   of C14 the remaining work in item 1 cannot be specified without it.

**Pre-authorised without the ruling: T6 only.** It is probe-only, sandbox
fixture only, changes no `flexicon/` behaviour, and it sharpens the ruling
itself by settling which rival mechanism holds (decisively, whether the data
is already gone before `CloseProject()` is entered) and by finding T7's
detector. If the user prefers "probe first, then rule", T6 can be greenlit
alone. It does not unblock T7 or T5.

**When the ruling lands:** T6 -> T7 -> T5, in that order. Do not start T5
first; its wording depends on both.

**Standing prohibitions, unchanged:** do NOT re-attempt T2 (C12); do NOT
reopen C1-C15, Q1 or Q3; do NOT touch `SaveChanges()`; do NOT file GitHub
issues inside the loop.

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
