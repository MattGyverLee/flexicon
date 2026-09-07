# STATUS -- 243-closeproject-save-guard (flexicon#243)

**Campaign:** `tier1-silent-data-loss`, queue item 1 of 4 -- **`done`.**
**Last updated:** 2026-09-07, end of spurt 9 (cycle 9) -- **CLOSING ENTRY.**
**Status:** **`feature_complete` (APPROVED by `/lex-lead`, cycle 9).** No
task remains open; every quality gate is green with live evidence on file.
The user's coupled ruling landed as `spec.md` C20 at spurt 6, the guard it
approved shipped at T8a/T8b (spurt 6/7), T7 and T5b landed at spurt 8, the
QC gate ran at spurt 9 (score 90/100, **P0 count 0**) and **both of its P1s
are now disposed** -- the fail-open one remedied by T9a/T9b this cycle, the
P-11 one ruled no-action with a forward rule (C28). C30 rules the last P2
(the pinned source-slice window) out of this feature and into QUEUE.md as
an ungated cleanup. **THE RALPH LOOP REMAINS CANCELLED** -- the Stop hook
will not re-feed anything; each spurt since spurt 5 is a directed dispatch,
not a loop iteration.

> **THE CAMPAIGN IS NOT COMPLETE.** Item 1 closing is not
> `TIER1 COMPLETE`. Queue items 2 (#242), 3 (the feature-structure bundle
> #251/#252/#253/#256) and 4 (#250) are untouched and still `queued`. No
> promise token was emitted at this closure, by design.
>
> **GitHub #243 is deliberately still OPEN.** The crew does not file or
> close issues; and per C10 the `.fwdata` file-swap half of the owner's
> report is unmeasured and unexplained by design, so closing the issue is
> the user's call, not a consequence of this sign-off.

> ## THE ONE FACT THIS FEATURE TURNS ON (C17, measured at T6 -- NOW MET BY T8b)
>
> **No `CloseProject()`-side change could ever fix the owner's filed
> incident, at any price, and none did.** T6/P-7 measured the 25 entries as
> already gone from the **still-open** project immediately after
> `SaveChanges()` raised -- **before `CloseProject()` is ever entered.** So
> no `CloseProject()`-side change -- not T3's shipped guard, not T7, not any
> future guard there -- could ever recover that data. **C17 named the only
> remaining route as the `SaveChanges()` depth guard, and T8b (spurt 7)
> shipped exactly that:** the full owner sequence now re-measures **25/25 in
> memory and 25/25 on disk** (`evidence/live-t8b-savechanges-guard.md`).
>
> **And, unqualified: T3 IS a real, shipped, live-verified fix for the P-3
> path** (intact change set + stray/forced `End`): 0/25 -> 25/25. C17 does
> not weaken that.
>
> **Say all three things together: T3 fixed P-3; nothing in `CloseProject()`
> could ever have fixed the owner's real P-5 -> P-3 chain; T8b, on the
> `SaveChanges()` side, has now fixed that chain too.** Any one alone is a
> misrepresentation.

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

## What landed in spurts 6-9 (cycles 6-9) -- the blocker resolved, the guard shipped, closure gated on one small task

**Spurt 6 (cycle 6):** the user ruled on the blocker directly, frozen as
`spec.md` **C20** -- the `SaveChanges()` guard is APPROVED IN SUBSTANCE,
constrained to depth/transaction correctness only, not sharing exclusivity.
**T8a** (measurement-only, zero `flexicon/` diff) then proved a blanket
`CurrentDepth > 0` guard is safe: no measured case exists where
`SaveChanges()` currently succeeds at depth > 0. Frozen as **C21**.

**Spurt 7 (cycle 7):** **T8b landed** -- `SaveChanges()` now raises
`FP_TransactionError` before `usm.Save()` at any `CurrentDepth > 0`, mode-
differentiated message, fails OPEN on an unreadable depth. All three
shipped docstring `Example`s corrected in the same diff; all 11 enumerated
test sites (`spec.md` C22) repaired. **Headline: the full owner sequence now
re-measures 25/25 in memory and 25/25 on disk**, meeting C17's ceiling from
the only side C17 said could ever meet it. A new probe, **P-11**, found an
escaping `FP_TransactionError` inside `UndoableOperation()` did NOT discard
the block's object creations (25/25 survived) -- contradicting that
module's own rollback docstring; routed, not absorbed, per `spec.md` C25.
`/lex-lead` recut T7 as **C23**: post-T8b the only live route into
`CloseProject()`'s Phase-1 branch is the one where the save already
succeeded, so T7's planned `FP_ProjectError` raise is WITHDRAWN; the
ERROR-level log is the whole remaining remedy.

**Spurt 8 (cycle 8):** `/lex-doc` closed out T5b --
`CHANGELOG.md` corrected (**C24**: the pre-existing "this does not fix the
incident #243 was filed about" text was FALSE as of T8b and is replaced),
`docs/TRANSACTION_GUIDE.md` corrected (inverted "no side effects" claim, an
accuracy banner on the unverified Phase 1 rollback narrative, mode notes on
both usage examples), Q4 CLOSED, C25's narrow routing recorded, a C22 table
correction (**C26**), and a standing staleness-sweep rule (**C27**). **T7
landed the same cycle** via `/lex-programmer`: probe 11/11 live,
`test_abort_session_live.py` 12/12, both `run_mode: live`; offline
1291 passed (1290+1), deselected 475 unchanged. See
`specs/243-closeproject-save-guard/reviews/cycle8-doc.md`,
`reviews/cycle8-programmer.md` and `spec.md` C20-C27.

**Spurt 9 (cycle 9): the cycle-8 QC gate ran, and its two P1s were ruled.**
`lex-verification` audited T8b's shipped guard as a read-only
claims-vs-evidence check, substituting for the unregistered `lex-qc` agent
type -- a substitution `/lex-lead` accepted because the gate's content was
delivered regardless of the agent name (`reviews/cycle8-qc.md`). Score
90/100, **P0 count 0**. Two P1s: (1) `SaveChanges()`'s fail-open catch
(`FLExProject.py:845-856`) is broader than its own justification -- it
catches any exception from the depth read, but C21's reasoning covers only
the one documented `FP_ProjectError` case, and no test exercised the
fail-open branch at all; (2) the P-11 prediction-before-measurement claim
cannot be proven from git history because T8b landed as one uncommitted
diff. Ruled as **C28**: the catch is NOT narrowed and C21's fail-open
policy is NOT reopened -- narrowing on unmeasured exceptions would itself
be a new, speculative behaviour change, the same failure mode as
C11/C12/C14. Instead the DOCUMENTED contract is broadened to match the
code (**T9a**) and the missing offline test is added (**T9b**); the
residual (an unmeasured exception where `ObjectRepository()` does NOT also
raise) is named, not resolved. P-11's prediction claim: NO ACTION -- it
triangulates from three independent sources (C21 frozen before T8b ran,
`/lex-lead`'s own witnessed dispatch brief, and the P-11 test's
dynamically-branching verdict), stronger than a git timestamp. A second
finding -- the cycle-8 programmer's `transaction.py:146-153`
counter-measurement, a live measurement where rollback DID discard a
created POS, opposite of P-11's 25/25 survival -- was ruled as **C29**:
protected as a true record like C10, not folded into C25's existing queue
bullet, given its own "Awaiting user approval" line in the campaign
`QUEUE.md` naming the uncontrolled variables (object type, helper class,
exit path, envelope state). Full detail: `spec.md` C28/C29;
`reviews/cycle9-doc.md`. **One task remains: T9** (`tasks.md` CP-CLOSE) --
once it lands, item 1 is a candidate for `/lex-lead`'s final sign-off.

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
- **Q5** -- **FULLY CLOSED.** Detector half RESOLVED spurt 5 as **C18**;
  ruling half RESOLVED spurt 6 as **C20** (the user approved the
  `SaveChanges()` guard). Nothing remains open under Q5.
- **Q4** -- **CLOSED spurt 8** by `/lex-doc`: amend the existing
  `[Unreleased]` entries in place, cross-referencing `[4.4.0]` by prose,
  not a new heading or a forward pointer. See `spec.md` Q4.

Nothing remains genuinely open except T7's and T5b's own completion this
cycle (tracked in `tasks.md`, not here).

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

C1-C10 (spurt 1), **C11** (spurt 2), **C12** (spurt 3, T2 dropped),
**C13/C14/C15** (spurt 4), **C16/C17/C18/C19** (spurt 5), **C20/C21**
(spurt 6, the user's ruling and the T8a guard-shape measurement),
**C22/C23** (spurt 7, T8b's test blast radius and the T7 recut),
**C24/C25/C26/C27** (spurt 8, the CHANGELOG correction, P-11 routing, the
C22 table correction, and the staleness-sweep rule), and **C28/C29**
(spurt 9, this pass -- the cycle-8 QC gate's two P1s: the `SaveChanges()`
fail-open catch's contract/coverage, and the `transaction.py`
counter-measurement's own queue line). Do not reopen any of them;
overturning any specific decision requires citing and overturning it
explicitly. Note that **C18 supersedes C14 point 3**, **C16/C17 answer
C13's "NOT frozen" paragraph**, and **C26 supersedes C22's table** (read
those originals as history).

## Closure entry (spurt 9, cycle 9) -- what landed and what is NOT claimed

**T9a** rewrote the `SaveChanges()` fail-open comment to describe the
`except Exception` catch the code actually has (ANY depth-read exception
fails open, per C21), labelled the measured-safe case as CODE INSPECTION
rather than a live probe, and named the un-measured residual per C10's
discipline -- claimed neither safe nor a bug. **Zero executable-line
change, confirmed by diff.** **T9b** added the one offline test that
exercises that branch, forcing `CurrentDepth` to raise a `RuntimeError`
(deliberately not `FP_ProjectError`) and asserting the WARNING fires,
`SaveChanges()` does not raise, and **`usm.Save()` is called exactly
once** -- that third assertion is the point: it pins fail-open so a future
silent flip to fail-closed cannot pass green.

Gates at closure: collect-only 11 and 12 as predicted; live **11/11** and
**12/12**; `tests/live_status.json` `"run_mode": "live"`; offline suite
**1292 passed / 475 deselected**. One honest prediction miss is on the
record and was reported rather than smoothed: the dispatch brief predicted
the deselected count moving 475 -> 476. It did not, and could not -- a new
test WITHOUT `requires_live_project` lands in the `passed` bucket, while
`deselected` counts only what the marker filter excludes. **The brief's
prediction was wrong; the measurement is right.** Kept visible as the C28
forward rule working exactly as intended.

**Still NOT claimed, at closure:** the `.fwdata` file-swap half of the
owner's report (C10 -- out of scope, unexplained by design, never claimed
fixed); the fail-open branch's un-measured residual (C28); and any
generalisation of P-11 into "rollback never discards" (C29's
counter-measurement is precisely what forbids it).

## Next pickup -- NOT this feature

**Item 1 is closed.** The next pickup is a CAMPAIGN-level decision, not a
task here: queue item 2 (`242-paragraph-whitespace`) is next in
`specs/tier1-silent-data-loss/QUEUE.md`, and **no work on it was authorised
by this closure.** Do not reopen this feature to do it. The two items
awaiting the user's approval (C25/P-11 and C29's counter-measurement) plus
C30's ungated test-harness cleanup are all recorded in QUEUE.md.

## Historical -- the blocker that was resolved at spurt 6

**The blocker is RESOLVED.** The user ruled (C20, spurt 6); the guard the
ruling approved shipped (T8a/T8b, spurt 6/7); the owner's filed incident
now measures 25/25 (see the banner above). Nothing is `needs_human` on this
feature any more. **The ralph loop remains CANCELLED regardless** -- each
spurt is still a directed dispatch, not an automatic re-entry; a human (or
`/lex-lead`, dispatched by a human) drives the remaining steps.

**T7 and T5b LANDED at spurt 8.** The cycle-8 QC gate then ran (spurt 9,
score 90/100, P0 count 0) and its two P1s are ruled as **C28/C29** (this
pass). **Work done at spurt 9 -- CP-CLOSE / T9, now LANDED (read as history):**

1. **T9a** (docs/comment only, zero executable change) -- broaden the
   `SaveChanges()` fail-open catch's documented contract to match the
   shipped code, per C28.
2. **T9b** (offline test) -- add the one missing test exercising the
   fail-open branch, per C28.

**Standing prohibitions, unchanged:** do NOT re-attempt T2 (C12); do NOT
reopen C1-C30 without citing and overturning the specific decision; do NOT
touch `SaveChanges()`'s fail-open POLICY (only its documented contract and
test coverage, per C28); do NOT file GitHub issues inside the loop.

**T9 landed and was verified, and `/lex-lead` signed the feature off at
cycle 9 (APPROVED).** Q2, Q3, Q4 and Q5 were already CLOSED; no open
question remained.

## Routed to the user (do not act on inside the loop)

**RESOLVED at spurt 6 -- kept here as the audit trail, not an open item.**
The `SaveChanges()` depth guard this section used to describe as awaiting
the user's ruling was APPROVED (`spec.md` C20) and has LANDED (T8a/T8b).
See `specs/tier1-silent-data-loss/QUEUE.md` -> "Awaiting user approval" for
the full history and the ONE genuinely new item spawned this cycle
(**C25**): whether `UndoableUnitOfWorkHelper.Dispose()` +
`set_RollBack(True)` actually discards property modifications or deletions
-- object creation is already MEASURED (25/25 survived, T8b's P-11), but
property modifications and deletions are unmeasured. That question is out
of #243's scope and awaits its own user approval; nothing in this feature
is blocked on it.

**A SECOND item was spawned at cycle 9 (`spec.md` C29):** a counter-
measurement at `transaction.py:146-153` where the same `Dispose()`-with-
`RollBack`-effectively-`True` mechanism DID discard a created object (a
POS vanished on clean exit), the opposite of P-11's 25/25 survival. It is
protected as a true record (do not edit it) and given its own queue line
rather than folded into the C25 bullet above, naming the discriminating
variables (object type, helper class, exit path, envelope state) that
would need controlling to reconcile the two. Nothing in this feature is
blocked on it either.
