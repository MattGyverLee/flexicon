# TASKS -- 243-closeproject-save-guard

Derived from `spec.md` sections 3 and 6 (C1-C10). Issue: #243.

**CHECKPOINT NUMBERING -- read this first.** The campaign
(`specs/tier1-silent-data-loss/QUEUE.md`) called the spec+probe milestone
"Checkpoint 1"; that milestone is DONE (spurt 1, 2026-09-07) and is NOT any
of the checkpoints below. The three checkpoints in this file are the
IMPLEMENTATION checkpoints and start after it. To remove the collision they
are referred to as **CP-A (T1-T2)**, **CP-B (T3-T4)** and **CP-C (T5)**;
the older "Checkpoint 1/2/3" headings below are retained only so existing
cross-references still resolve. T1 is DONE (spurt 2). **T2 is DROPPED (spurt 3
-- spec.md C12); CP-A is CLOSED in full. The next spurt starts at CP-B / T3.**

**Q1 is CLOSED (spec.md C9/C10, ruled 2026-09-07).** No task below may
reopen it, and no task may wait on owner repro steps -- the owner's
sequence is reconciled as a P-5 -> P-3 chain that the C6 guard breaks.

**Q3 is now ALSO CLOSED (spec.md Q3, ruled 2026-09-07 at T1): NO capability
token.** `flexicon/__init__.py` and
`tests/write_path_transactions/test_capabilities.py` are out of scope for
every task below. **Q2, Q3, Q4 and Q5 are now ALL CLOSED** (see the "STATE
AS OF SPURT 8" block below for the current tally -- this paragraph is
retained as history of when Q1/Q3 first closed).

**STATE AS OF SPURT 8 (cycle 8, 2026-09-07) -- READ BEFORE ANY TASK BELOW.**
Done: T1, T3, T4, T6, **T8a, T8b**. Dropped: T2 (C12). **The user's coupled
ruling landed as C20 (spurt 6) -- T7 is no longer blocked.** In progress
THIS CYCLE: **T7** (the C23-recut loudness log, dispatched to
`/lex-programmer` in parallel) and **T5b** (this docs pass, `/lex-doc`).
T5a already landed as a pre-authorised unit (see Checkpoint 3). **T7 and T5b
LANDED at spurt 8** (see `STATUS.md`). Contract is
now **C1-C30** (spurt 9, cycle 9: **C28/C29** on the cycle-8 QC audit's two
P1 findings, plus **C30** at closure ruling the pinned source-slice window
P2 out of this feature and into QUEUE.md as an ungated cleanup). **T9a/T9b
LANDED at spurt 9 -- CP-CLOSE reached; item 1 is CLOSED.** Q2 CLOSED (C15); Q3 CLOSED (no capability token);
**Q4 CLOSED** (spurt 8, `/lex-doc`'s placement/wording call); **Q5's
detector half CLOSED (C18)**, its ruling half CLOSED (C20). **THE RALPH LOOP
IS STILL CANCELLED** -- no Stop hook re-feeds anything; each spurt is a
directed dispatch, not a loop iteration. **C17's ceiling still stands as
written -- no `CloseProject()`-side change could ever fix the owner's
filed incident -- but T8b has now DONE it from the `SaveChanges()` side
C17 said was the only possible route:** the full owner sequence (create,
mid-session `SaveChanges()`, `CloseProject()`) re-measures **25/25 in
memory and 25/25 on disk** (`evidence/live-t8b-savechanges-guard.md`), up
from 0/25 pre-guard. T3's independent P-3 fix (0/25 -> 25/25) still stands
as shipped. State all three facts together, not any one alone. **The only
remaining task is T9** (below, CP-CLOSE) -- the last thing between item 1
and closure.

**New contract decision C11 (spec.md, ruled 2026-09-07 at the T1 review):**
`HasOpenSessionTask()` reads depth BEFORE the `self._undoable` mode check,
because C4's closed/never-opened `FP_ProjectError` has no mode carve-out and
because `self._undoable` does not exist on a never-opened instance. Do not
reorder it. T3 must consume the surface as shipped.

**CP-A IS CLOSED IN FULL (spurt 3, 2026-09-07).** T1 landed alone (CP-A1);
T2 was gated into CP-A2 and is now **DROPPED ON THE MERITS** -- see `spec.md`
**C12**, `reviews/cycle3-programmer.md` and
`evidence/live-t2-internal-callsite-dedup.md`. Read CP-A below as
**CP-A1 = T1 (DONE)** and **CP-A2 = T2 (DROPPED -- closed on a finding, zero
diff in `flexicon/`)**. **CP-B is UNBLOCKED and is the next pickup.** C6's
prerequisite was always the PUBLIC depth-read surface, which T1 alone
delivered; C5 itself made the internal-call-site consolidation optional, and
C12 declines that option permanently. **Do NOT re-attempt T2** -- three
independent attempts are already on file with their failure counts.

**Ordering rule (binding):** P1 (the depth-read surface) is a PREREQUISITE of
P0's final shape, not a follow-on -- `spec.md` C6. Tasks below are sequenced
accordingly: the depth read lands first, then the guard that consumes it,
then the CHANGELOG entry.

**Extend, do not duplicate:** `tests/operations/test_issue243_closeproject_probe.py`
already exists from Checkpoint 1 (5 live tests passing against the UNFIXED
code -- P-1 through P-5). Every task below that needs a regression test
EXTENDS this file in place; it does not create a parallel probe file. In
particular, `test_p3_p6_reproduction_and_symptom` and
`test_p5_save_before_forced_end` become the regression tests for the P0
guard once the fix lands -- their assertions flip from "0 survivors, raise
expected" to "N survivors, no raise" against the patched `FLExProject.py`.

**Live verification boilerplate (applies to every task marked LIVE below):**
use the `target_sandbox` / `target_sandbox_path` fixture ONLY -- never the
real Target, never a `scripts/restore_*.py` run. Exact invocation:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
```

(never bare `pytest`, never `--ignore=tests/contract`). Write an evidence
file at `specs/243-closeproject-save-guard/evidence/live-<task>.md` with the
exact command, the `run_mode` value from `tests/live_status.json`, and
pre/post values RE-READ from the LCM (re-querying after the write, not
asserting on the value passed in).

**LIVE SET RE-DERIVED FROM MARKERS, NOT FILENAMES (spurt 3, 2026-09-07 --
binding for T3/T4).** T2's brief named three "live suites" chosen by filename.
One of them, `tests/operations/test_transaction_rollback.py`, carries **zero**
`requires_live_project` markers -- it is a fully offline Mock/patch file
despite its name, and it collected **0 tests** under `-m requires_live_project`
(`20 deselected`). A second, `test_custom_field_multistring_best_alt.py`,
`1 skipped` on a pre-existing environment-dependent skip. So only one of the
three named files verified anything. **Never name a live suite by its
filename again.** Derive it, and paste the derivation into the evidence file:

```
python -m pytest <file> -m requires_live_project --collect-only -q
```

A file that reports `no tests collected` is NOT a live pass -- it is zero
tests, and reporting it as green is a false verification claim. Counts
confirmed at the cycle-3 review:

| File | Live tests collected | Use for |
|---|---|---|
| `tests/operations/test_issue243_closeproject_probe.py` | **6** (module-level `pytestmark`) | T3/T4 PRIMARY -- extended in place by T4 |
| `tests/operations/test_undoable_mode_live.py` | **33** | T3 regression: the mode/depth/session-envelope path |
| `tests/operations/test_target_live_smoke.py` | **3** | T3 regression: canonical open/close lifecycle |
| `tests/operations/test_transaction_rollback.py` | **0** -- OFFLINE FILE | run OFFLINE only (20 tests, `-m "not requires_live_project"`); it IS the real coverage of the rollback path |
| `tests/operations/test_custom_field_multistring_best_alt.py` | 1, env-skips here | do NOT rely on it as a gate |

T3/T4's live gate is therefore: probe (6, growing with T4) + 33 + 3, all
green with `run_mode: live`, PLUS the offline suite at `1290 passed` (the
frozen pre-T1 baseline, unchanged through T1 and T2) via
`python -m pytest tests -m "not requires_live_project" -q`. T5 is DOCS-ONLY
and stays live-exempt -- no derivation needed there.

---

## Checkpoint 1 -- P1: the depth-read surface (T1-T2)

Prerequisite for everything else per C6. Touches
`flexicon/code/FLExProject.py` only.

- [x] **T1** (LIVE) **DONE 2026-09-07 (spurt 2, cycle 2).** Add a private depth-read helper on `FLExProject` (e.g.
      `_ReadActionHandlerDepth()`) that raises `FP_ProjectError` when
      `self.project` does not exist (closed or never opened -- C4), and
      otherwise returns `self.project.ActionHandlerAccessor.CurrentDepth`
      verbatim, with NO lenient `except: return 0` fallback (C5). On top of
      it, add the public surface:
      - `CurrentDepth` (property or method -- implementer's choice, state
        which in the task report): raw `int` passthrough via the helper.
        `writeEnabled=False` returns the real value (`0`) without raising
        (C4); closed/never-opened raises `FP_ProjectError` (C4).
      - `HasOpenSessionTask()`: unconditionally `False` when `self._undoable`
        is `True` (C3); otherwise `CurrentDepth > 0` via the same helper
        (so it inherits the same open/closed raise behaviour).
      Live-verify against the frozen P-2 table in `spec.md` section 2: EXTEND
      `test_p2_depth_table` (or add a new test function in the same probe
      file) to call the new public `CurrentDepth`/`HasOpenSessionTask()` and
      assert they match every row of that table, PLUS two new cases the
      original P-2 probe did not need to assert on: (a) calling either
      method after `CloseProject()` has succeeded (project closed) raises
      `FP_ProjectError`; (b) calling either method on a `FLExProject()`
      instance on which `OpenProject()` was never called raises
      `FP_ProjectError`. Command and evidence file per the boilerplate
      above; evidence file name `live-t1-depth-read-surface.md`.

      **T1 OUTCOME (verified by `/lex-lead`, not taken on report):**
      `_ReadActionHandlerDepth()`, `CurrentDepth` (implemented as a
      **property**, matching the `Cache` property precedent) and
      `HasOpenSessionTask()` are in `flexicon/code/FLExProject.py`. Live
      probe 6/6 green with `tests/live_status.json` `"run_mode": "live"`;
      offline suite 1290 passed (unchanged baseline); all 8 frozen P-2 rows
      plus both new closed/never-opened `FP_ProjectError` cases match the
      frozen contract exactly. `git diff --stat flexicon/code/` = 120
      insertions, 0 deletions, ONE file -- purely additive, so
      `CloseProject()` (T3) and `SaveChanges()` are provably untouched. C5
      holds: no `except: return 0`, no `getattr(..., 0)` in the helper.
      Q3's NO ruling honoured (neither `__init__.py` nor the capabilities
      test was touched). One deviation from the dispatch brief was reviewed
      and CONFIRMED as correct, now frozen as **spec.md C11**.
      Evidence: `evidence/live-t1-depth-read-surface.md`.
      Report: `reviews/cycle2-programmer.md`.
- [~] **T2** (LIVE) **DROPPED 2026-09-07 (spurt 3, cycle 3) -- see `spec.md`
      C12. Closed on a FINDING, not a diff. Do NOT re-attempt; do NOT re-tick
      as open work after a context reset.** The task as specified was: point
      the three existing internal lenient call sites
      (`transaction.py:172`, `undoable_operation.py:102`,
      `System/CustomFieldOperations.py:306`, all currently
      `getattr(action_handler, "CurrentDepth", 0)` or equivalent) at T1's
      shared private helper, keeping each call site's own local
      `try/except`/`getattr` fallback WRAPPED AROUND the helper call (not
      removed) so their tolerance for incomplete test doubles is preserved
      (C5 -- the lenient fallback stays out of the public surface, not out
      of existence). Behaviour-preserving; zero functional delta for these
      three sites. Live-verify by running the existing live suites that
      exercise these three files unchanged: `tests/operations/test_transaction_rollback.py`,
      `tests/operations/test_custom_field_multistring_best_alt.py`, and
      `tests/operations/test_undoable_mode_live.py`, each via:
      ```
      $env:FLEXLIBS_REQUIRE_LIVE = "1"
      python -m pytest tests/operations/test_transaction_rollback.py -m requires_live_project -q
      python -m pytest tests/operations/test_custom_field_multistring_best_alt.py -m requires_live_project -q
      python -m pytest tests/operations/test_undoable_mode_live.py -m requires_live_project -q
      ```
      All three must stay green, unchanged pass counts vs. pre-T2. Evidence
      file `live-t2-internal-callsite-dedup.md` records all three commands,
      `run_mode`, and before/after pass counts (this task's "pre/post value"
      is the pass count, not an LCM read, since it is a behaviour-preserving
      refactor with no new state to assert on).

      **T2 OUTCOME -- DROPPED (ruled by `/lex-lead`, cycle 3; claims verified,
      not taken on report):** all three sites were attempted with the
      prescribed wrapped-lenient shape and each broke the offline suite
      (`transaction.py:172` -> 9 failed; `undoable_operation.py:102` -> 2
      failed; `System/CustomFieldOperations.py:306` -> 2 failed). All three
      were reverted; `git diff f3a0f50 -- flexicon/` is EMPTY (independently
      re-verified at the cycle-3 review) and the offline suite is 1290 passed
      before and after, i.e. the pre-T2 baseline. **The premise was wrong:**
      the strict helper (raises `FP_ProjectError`, returns depth verbatim --
      C5) and the three lenient sites (coerce non-`int` to `0` to tolerate
      doubles) want DIFFERENT contracts, so sharing one implementation is a
      conflation, not a de-duplication. Both escape hatches are REJECTED with
      the full reasoning in `spec.md` C12; the decisive point is that the
      prescribed `except` wrapper would swallow the `FP_ProjectError` the
      helper exists to raise and substitute `0`, which at
      `CustomFieldOperations.py:306` silently disables the issue-#21
      corruption guard. Adding `spec=` to the doubles is NOT deferred and NOT
      owed as a follow-up -- T2 is dropped on the merits, so the enabling
      test change has no purpose. Nothing in P0/P1/P2 depends on T2.
      Evidence: `evidence/live-t2-internal-callsite-dedup.md`.
      Report: `reviews/cycle3-programmer.md`.

**Checkpoint CP-A1 (T1) -- REACHED 2026-09-07 (spurt 2).** `FLExProject`
exposes `HasOpenSessionTask()`/`CurrentDepth` matching the frozen P-2 table
exactly, including both new closed/never-opened raise cases, live-verified
with `run_mode: live` and zero offline regression. C6's PUBLIC-SURFACE
prerequisite for the P0 guard is satisfied by T1 alone.

**Checkpoint CP-A2 (T2) -- CLOSED 2026-09-07 (spurt 3) ON A FINDING.** The
exit condition as originally written (three sites delegating to T1's helper)
is UNREACHABLE and has been withdrawn -- `spec.md` C12. CP-A2's actual, met
exit condition is: the delegation was attempted at all three sites, empirically
shown to break the offline suite, fully reverted (zero diff in `flexicon/`),
the offline baseline re-confirmed at 1290 passed, and the finding frozen as a
contract decision so it is not rediscovered. CP-A is closed; CP-B is open.

**Why T2 did not block CP-B** (retained for the record; T2 is now dropped
outright per C12, so this paragraph's conclusion stands with the stronger
reason that there is no longer any T2 to block anything). C6's prerequisite is the PUBLIC depth-read
surface, which T1 delivers; C5 itself calls the internal-call-site
consolidation optional ("optionally, at the implementer's discretion during
T2"). T2 is a behaviour-preserving refactor of three files T1 never touched.
It is nonetheless sequenced BEFORE CP-B on purpose: it is the cheapest
possible confirmation that the new helper survives real internal callers,
and running it after the P0 guard would mix a refactor into the diff that
carries the actual fix. Do CP-A2 next; do not skip it to reach T3 sooner.

At each of CP-A1/CP-A2: stop, update `STATUS.md` / `.crew-handoff.json` and
the campaign `QUEUE.md` / `.crew-handoff.json`, commit.


---

## Checkpoint 2 -- P0: the CloseProject() End-guard and its regression tests (T3-T4)

Consumes T1's public surface per C6. Touches `flexicon/code/FLExProject.py`
only.

- [x] **T3** (LIVE) Implement the C1/C6 guard around
      `CloseProject()`'s line-326 `EndNonUndoableTask()` call:
      1. Before attempting the call, check `self.HasOpenSessionTask()` (or
         the equivalent `CurrentDepth > 0` read via T1's helper). If no
         envelope is open, skip the call and log at debug level rather than
         assuming the mode implies the envelope's presence.
      2. When the check says an envelope IS open, still wrap the
         `EndNonUndoableTask()` call itself in try/except or try/finally so
         that ANY raise from it -- not just the depth-0 case the check
         already prevents -- cannot skip line 332's `usm.Save()`.
      Do NOT reorder lines 326/332 (C7 -- End-then-Save order is unchanged).
      Q1 is CLOSED (C9/C10) -- implement against it, do not reopen it. Leave
      Q2 (should the whole `CloseProject()` body get a `try/finally` so
      `Dispose()` always runs?) as open follow-up, not blocking this task;
      do not silently resolve it while implementing T3. If implementation
      reveals a concrete answer, record it as a new dated note under Q2 in
      `spec.md`, do not just change the code and move on.
- [x] **T4** (LIVE) EXTEND the probe file's own regression tests to prove T3
      fixes the bug:
      - `test_p3_p6_reproduction_and_symptom`: re-run the exact P-3 sequence
        (create 25 entries, manually end the envelope early, call
        `CloseProject()`) against the PATCHED code. Flip the assertions: no
        raise expected from `CloseProject()`, and reopening the same
        `.fwdata` read-only must show 25/25 survivors (re-read from the LCM,
        not asserted from the in-memory create calls). Keep the original
        unfixed-code behaviour documented in a comment for historical
        record, but the live assertions must reflect the fixed contract.
      - `test_p5_save_before_forced_end`: re-run the exact P-5 sequence
        (create 25 entries, call `SaveChanges()` while `CurrentDepth=1`,
        then force the early End, then `CloseProject()`). Per the C1 verdict,
        `SaveChanges()` itself still raises at `CurrentDepth > 0` (T3 does
        not touch `SaveChanges()`), so this test's assertion on
        `SaveChanges()`'s own raise is UNCHANGED (T3 does not touch
        `SaveChanges()`).

        **RAISED BAR, per the C9 ruling (2026-09-07).** The earlier wording
        here asked only that the guarded `CloseProject()` "not compound the
        loss." That is too weak: C9 establishes that P-5 is the TRIGGER of
        the owner's real incident and P-3 its loss mechanism, so P-5's
        post-guard outcome IS the acceptance test for the owner's actual
        sequence, not a side note. The assertion is therefore a MEASURED
        survivor count, re-read from the LCM after a read-only reopen:
        - The guard's intent is **25/25 survivors**. After `SaveChanges()`
          raises, depth is 0 (measured in cycle 1) and the 25 entries are
          still in the in-memory cache, so the guard should skip the End
          and reach `usm.Save()` at a legal depth.
        - **Do not assume it -- measure it.** If the count is 0/25, then a
          `UnitOfWorkService` whose commit check has already failed is
          unrecoverable, and that is a NEW finding: record it as a dated
          note under `spec.md` Q2 and report it to `/lex-lead`. It would
          mean the owner's sequence needs a companion guard on
          `SaveChanges()` itself -- the follow-up already routed to
          QUEUE.md "Awaiting user approval". Do NOT silently expand scope
          to add that guard inside T3/T4.
        - Any intermediate count (1..24) is a partial-write finding and is
          itself P0-severity -- report it, do not paper over it.
        State in the test's docstring exactly which part of P-5's outcome
        T3 does and does not change.
      Command and evidence file per the boilerplate above; evidence file
      name `live-t4-p0-guard-regression.md`, explicitly quoting the before
      (unfixed, from `evidence/live-cycle1-probe.md`) and after (fixed)
      survivor counts for both P-3 and P-5.

**CP-B ENTRY NOTE (spurt 3).** CP-B is UNBLOCKED as of 2026-09-07: T1
shipped the public surface C6 requires, and T2 is dropped (C12). Start at T3.
Use the re-derived live set in the boilerplate section above -- probe (6) +
`test_undoable_mode_live.py` (33) + `test_target_live_smoke.py` (3) -- and run
`test_transaction_rollback.py` OFFLINE. Q2 is still OPEN and T3 is where it
gets decided: record the decision as a dated note under `spec.md` Q2, do not
just change the code. **`SaveChanges()` remains untouchable** -- its missing
depth guard is a behaviour change awaiting the USER's ruling in the campaign
QUEUE.md; T3 must not add, plan or prototype it, and T5 may only fix its
docstring prose.

**Checkpoint:** T3 landed, T4's extended P-3 and P-5 tests both green
against the patched `FLExProject.py`, `test_p1_mode_matrix` and
`test_p2_depth_table` (unaffected by T3) still green, `test_p4_control_run_normal_close`
still green. Full extended probe file run
(`python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s`)
shows all tests passing with `run_mode: live`. Update `STATUS.md` /
`.crew-handoff.json`, commit. Acceptance criteria 1, 2, 3, 4 in `spec.md`
section 5 are satisfied at this checkpoint.

**CP-B REACHED 2026-09-07 (spurt 4, cycle 4) -- PASSED, with two P1 defects
found by `/lex-lead` that are NOT T3 rework.** T3 and T4 both landed green:
probe 6/6, `test_undoable_mode_live.py` 33/33, `test_target_live_smoke.py`
3/3, all `run_mode: live`; `test_transaction_rollback.py` 20/20 offline;
offline suite unchanged at `1290 passed`. Acceptance criteria 1, 2, 3 and 4
are satisfied. **P-3: 0/25 -> 25/25 with no raise** -- the loss mechanism is
fixed, and the guard is correct-and-shippable on its own merits. **P-5
measured 0/25**, the branch T4 named in advance; frozen as **spec.md C13**
(what that measurement does and does not establish) and **C14** (it is a new
silent-loss surface). Two defects, both `/lex-lead`'s own to own:

1. **T3's brief was wrong**, not its implementation. "log at debug level"
   made the Phase-1 no-envelope branch -- which is anomalous by construction
   and means we are standing inside the owner's incident -- the quietest
   thing in the method. C14 remedies it at T7. Same class of brief-wording
   error as C11.
2. **T4's P-5 "CloseProject() did not raise" is unasserted and unquoted.**
   `test_p5_save_before_forced_end` captures `close_exc_msg` and never checks
   it (P-3 asserts it), and the evidence file transcribes pass-counts rather
   than the `[PROBE][P5]` console lines from its `-s` run. That claim is
   load-bearing for C13 fact 3 (silent no-op vs loud raise), so T6 must pin
   it.

**NEXT IS NOT T5.** New sequencing: **T6 (probe) -> T7 (the C14 loudness
remedy) -> T5 (CHANGELOG, LAST)**. T5's wording depends on T7's outcome and
on the user's ruling, so it cannot go first. **Item 1 is `needs_human` as of
this checkpoint** -- see the blocker in `.crew-handoff.json`; T7 must not be
designed before the user rules on the `SaveChanges()` fourth ask.

---

## Checkpoint 2c -- Q5: the no-op-save probe and the loudness remedy (T6-T7)

Opened by the CP-B ruling (spurt 4). Both tasks arise from `spec.md`
C13/C14/Q5. `SaveChanges()` remains untouchable throughout -- T6 only
OBSERVES it, T7 does not modify it.

- [x] **T6** (LIVE, probe-only -- **safe to run WITHOUT the user's ruling**)
      **DONE 2026-09-07 (spurt 5, cycle 5). Run as a one-shot on the user's
      greenlight, NOT inside the loop -- the ralph loop is CANCELLED.**
      Outcome summary (full ruling in `spec.md` **C16/C17/C18**; verified by
      `/lex-lead`, not taken on report): **mechanism (ii) CONFIRMED,
      mechanism (i) RULED OUT, (iii) indistinguishable from (ii) and left
      unresolved by design.** P-7 read **0/25** from the STILL-OPEN project
      before `CloseProject()` was ever entered -> **this settles #243's
      ceiling (C17): no `CloseProject()`-side change can EVER fix the
      owner's P-5 -> P-3 sequence; only the `SaveChanges()` fourth ask can.
      T3's P-3 fix (0/25 -> 25/25) is untouched and stands as shipped.**
      P-8: a fresh envelope after the failure committed 1/1, so the
      `UnitOfWorkService` is not globally poisoned. P-9: `HasUnsavedChanges`
      exists but is **INDISTINGUISHABLE** read after `Save()` -> C18
      re-scopes T7's detector (below). CP-B defect 2 CLOSED (`close_exc_msg`
      now asserted at probe line 575; `[PROBE][P5]` lines quoted verbatim).
      Probe 6 -> **9** live tests, all green, `run_mode: live`; offline
      1290 passed with deselected 470 -> 473 (exactly the +3 new live
      tests); **`git diff --stat -- flexicon/` EMPTY** -- independently
      re-verified, so T6 stayed ruling-independent as designed.
      Evidence: `evidence/live-t6-noop-save-mechanism.md`.
      Report: `reviews/cycle5-programmer.md`.
      Original task text follows for the record.
      Extend `tests/operations/test_issue243_closeproject_probe.py` in place
      with three probes that settle C13's open mechanism question and find
      T7's detector. Sandbox fixture (`target_sandbox_path`) ONLY; no
      behaviour change to any `flexicon/` file, so this task is
      ruling-independent and may be greenlit on its own.
      - **P-7 -- is the data still there?** Run the P-5 setup; after
        `SaveChanges()` raises at `CurrentDepth=1`, re-read the 25 `TEST_`
        entries from the STILL-OPEN project. Present => rival mechanism
        (ii) is ruled out (the change set survived into `CloseProject()`).
        **Absent => (ii) is CONFIRMED and no `CloseProject()`-side change
        can ever reach 25/25** -- report that immediately, it settles #243's
        ceiling.
      - **P-8 -- is the UOW globally poisoned, or only the existing dirty
        set?** After `SaveChanges()` raises, open a fresh
        `BeginNonUndoableTask()`, create ONE new `TEST_` entry, `End`, then
        `CloseProject()`, then reopen read-only and count. The new entry
        persists => not globally poisoned, so (iii)/(ii) over (i). Nothing
        persists => (i), session-wide poisoning.
      - **P-9 -- the detector, and CP-B defect 2.** Reflect over the live
        `IUndoStackManager` and record its actual member list in the
        evidence file; look for a "has unsaved / pending changes" read. If
        one exists, measure it immediately BEFORE and AFTER `usm.Save()` in
        both the P-4 control (a real save) and the P-5 sequence (the no-op
        save), and report whether the two are distinguishable. Also **add
        the missing `close_exc_msg` assertion to
        `test_p5_save_before_forced_end` and QUOTE the `[PROBE][P5]` console
        lines verbatim in the evidence file**, closing CP-B defect 2 and
        pinning C13 fact 3 as a measurement rather than an inference.
      Live gate per the boilerplate, re-derived with `--collect-only`
      (the probe file's count grows again here). Evidence:
      `evidence/live-t6-noop-save-mechanism.md`. Do NOT modify
      `SaveChanges()`, do NOT implement any part of T7 here, and do NOT
      change `CloseProject()`.
- [ ] **T7** (LIVE) **IN PROGRESS (spurt 8, cycle 8) -- dispatched to
      `/lex-programmer` in parallel with this docs pass.** RECUT 2026-09-07
      (spurt 7, cycle 7) by `spec.md` C23. No longer `needs_human` -- the
      user's ruling landed as C20. Sequenced to run AFTER T8b (Checkpoint
      2d, now DONE), because T8b's own P-5 re-run is the
      empirical check on this task's one remaining live route. Implement in
      `flexicon/code/FLExProject.py` only:
      1. the Phase-1 `else:` branch logs at **ERROR**, not `debug` --
         reworded per **C23** to name the anomaly
         (`HasOpenSessionTask()` read `False` inside Phase 1, unreachable by
         construction unless the envelope was already ended early) and
         state plainly that `usm.Save()` is proceeding anyway, asserting
         **nothing** about whether data was lost. Post-T8b the only live
         route into this branch is P-3 (envelope gone, change set intact,
         save SUCCEEDS), so the log must not imply loss.
      2. ~~raise `FP_ProjectError`~~ -- **WITHDRAWN by C23.** Post-T8b, the
         P-5 route that justified this raise is CLOSED (T8b's guard stops
         `SaveChanges()` from ever collapsing the envelope), the
         `AbortSession()`-reopen-failure route already raises
         `FP_ProjectError` from `AbortSession()` itself
         (`FLExProject.py:955-963`), and the one route that remains live
         (P-3) is a SUCCESSFUL save. A raise there would be a false alarm on
         success and would never fire on a real loss -- C18 point 4's
         prohibition, applied to ourselves. Do not reintroduce this raise
         without first citing and overturning C23.
      3. **DETECTOR -- unchanged from C18**, only its consequence changes
         (feeds a log line, not a raise). Binding shape, unchanged:
         - **PRIMARY, required:** the Phase-1-envelope-missing anomaly
           (`writeEnabled and not _undoable` and `HasOpenSessionTask()` is
           `False`), computable from T1's P1 surface.
         - **OPTIONAL, diagnostic only:** a *pre*-`Save()` `HasUnsavedChanges`
           read, logged inside that already-anomalous branch. MUST NOT gate
           anything and MUST NOT introduce a second code path -- it is a
           proxy for "did an End just succeed", not independent information
           (P-9).
         - **DO NOT OVER-CLAIM.** Do not word `HasUnsavedChanges == False`
           as "there is nothing pending to save" -- proven false-negative
           (P-9's no-op shape read `False` while all 25 entries still
           existed in memory).
      4. move `Dispose()` / `del self.project` into a `finally` per **C15**
         -- unchanged, independent of whether the branch raises or merely
         logs.
      5. ~~re-point T4's P-5 assertions~~ -- **VOID by C23.** T8b re-points
         them itself (`spec.md` C22 row 3), and to **25/25**, not to
         "raises, 0/25" -- there is no T7-side assertion flip left to make.
      Do NOT touch `SaveChanges()`. Evidence: `evidence/live-t7-loud-close.md`.
      **C14 and C17 are NOT reopened by this recut.** C14's diagnosis of the
      observability regression stands; C17's ceiling stands -- no
      `CloseProject()`-side change was ever going to fix the owner's
      original filed sequence, only T8b's `SaveChanges()`-side change could.
      **Only C14's remedy SHAPE narrows**, because T8b removes the loss path
      the raise was written to make audible.

**Checkpoint -- HALF REACHED 2026-09-07 (spurt 5).** T6 is DONE: three
probes green (probe file 9/9, `run_mode: live`), mechanism named
((ii) confirmed / (i) ruled out / (iii) undetermined -- `spec.md` C16),
ceiling frozen (C17), detector verdict ruled (C18), CP-B defect 2 closed,
zero `flexicon/` diff. **UPDATED 2026-09-07 (spurt 7, cycle 7):** the user's
coupled ruling landed as **C20** (the `SaveChanges()` fourth ask is APPROVED
IN SUBSTANCE), so T7 is no longer `needs_human`. It is instead **RESEQUENCED
to run AFTER Checkpoint 2d / T8b** -- see `spec.md` **C23** and the rewritten
T7 bullet below. CP-C (T5b) stays gated, now behind T7 (unchanged shape,
new reason); **T5a already landed as a pre-authorised unit -- see Checkpoint
3 below.**

---

## Checkpoint 2d -- T8a/T8b: the SaveChanges() depth guard (CP-D)

Opened by `spec.md` **C20** (spurt 6) as the campaign's fourth ask, approved
in substance and constrained to depth/transaction correctness, not sharing
exclusivity. T8a is the P-10 measurement that decides the guard's shape;
T8b implements it. **T7 (Checkpoint 2c above) is RESEQUENCED to run AFTER
T8b** -- see `spec.md` **C23** -- because T8b's own P-5 re-run is the
empirical check on T7's one remaining live route.

- [x] **T8a** (LIVE, measurement only) **DONE 2026-09-07 (spurt 6, cycle 6).**
      Measured `SaveChanges()`'s behaviour at `CurrentDepth > 0` in the one
      case P-5/P-7 never exercised -- inside `UndoableOperation()` under
      `undoable=True` -- alongside two controls, to decide whether a
      blanket guard is safe. Result table (full detail
      `reviews/cycle6-programmer.md`,
      `evidence/live-t8a-savechanges-depth-blast-radius.md`):

      | Case | Context / mode | Depth before `SaveChanges()` | Raised? | In-memory survivors | On-disk survivors |
      |---|---|---|---|---|---|
      | A | `UndoableOperation()`, undoable=True | 1 | YES (`Commit at wrong place.`) | 25/25 | 25/25 |
      | B | `Transaction()`, undoable=True | 0 | NO | 25/25 | 25/25 |
      | C | `Transaction()`, undoable=False | 1 | YES (`Commit at wrong place.`) | 0/25 | 0/25 |

      **Verdict: BLANKET GUARD SAFE.** No measured case exists where
      `SaveChanges()` currently succeeds at `CurrentDepth > 0` -- Case A
      raises but the edit survives by a mechanism independent of that
      specific call (the enclosing `UndoableOperation()` block's own clean
      `__exit__` commits regardless); Case C reproduces the destructive
      P-5/P-7 mechanism; Case B is outside the guard's domain (depth 0).
      Frozen as **C21**. Probe file 9 -> 10 live tests
      (`test_p10_savechanges_depth_blast_radius`, matrix-style over A/B/C).
      Live: 10 passed, `run_mode: live`. Offline: 1290 passed, unchanged
      (deselected 473 -> 474, exactly +1). `git diff --stat -- flexicon/`
      empty -- `SaveChanges()` and `CloseProject()` untouched, as required
      for a measurement-only task.
      Evidence: `evidence/live-t8a-savechanges-depth-blast-radius.md`.
      Report: `reviews/cycle6-programmer.md`.
- [x] **T8b** (LIVE) **DONE (spurt 7, cycle 7).** Implement the C21
      guard in `flexicon/code/FLExProject.py`'s `SaveChanges()` only:
      1. Before calling `usm.Save()`, read `CurrentDepth` via the existing
         T1 helper. If it raises (closed/never-opened project), log a
         WARNING and proceed to `usm.Save()` unguarded -- fail OPEN, per
         C21, mirroring `CustomFieldOperations.py:306`'s `getattr(...,0)`
         precedent.
      2. If `CurrentDepth > 0`, raise `FP_TransactionError` instead of
         calling `usm.Save()`. Blanket predicate, no mode exemption (C21).
      3. The exception message differs by mode (C21's MESSAGE CLAUSE): the
         `undoable=False` wording may name data loss (measured,
         P-5/P-7/P-10 case C); the `undoable=True` wording MUST NOT mention
         data loss or data risk (measured false-positive risk, P-10 case A).
      4. Correct the three shipped docstring `Example` blocks named in C21:
         `SaveChanges()` (~:745-750), `RefreshFromDisk()` (:792-797),
         `AbortSession()`'s `else:` branch (~:908).
      5. Work through the C22 11-site blast radius: public-API pins
         (rows 1-3, 8-9) keep calling `SaveChanges()` and are re-pointed at
         `FP_TransactionError`; liblcm-mechanism pins (rows 4-7, and half of
         row 10) switch to the raw `usm.Save()` accessor so they keep
         measuring what C13/C16/C18 actually rest on; row 10 additionally
         gains a new assertion for the public `FP_TransactionError` path;
         row 11 (`test_transaction_honesty.py:73`)'s 1000-character
         slice is widened, not routed around (see `spec.md` C26 --
         re-keyed; the "`:154`" line does not need widening, it is
         `test_transaction_body_always_passes_none_none`'s unbounded
         slice, untouched).
      6. Add **P-11**: with the new guard live, re-run P-10's case A
         (`SaveChanges()` inside `UndoableOperation()`) and measure --
         do not infer -- whether the new `FP_TransactionError` is caught by
         the harness's `_safe()` wrapper as before, and separately let it
         escape the `with` block once, on purpose, to confirm whether
         `UndoableOperation.__exit__` treats it as a rollback trigger
         (expected: yes, identical to today's behaviour with the raw liblcm
         exception -- C21's caveat). Record which of the two shapes was
         measured for each claim.
      Live verification: `target_sandbox_path` only,
      `FLEXLIBS_REQUIRE_LIVE=1`, `-m requires_live_project`, counts derived
      with `--collect-only` per the standing rule, `run_mode: live` in
      `tests/live_status.json`, offline baseline re-confirmed against 1290
      (T8a's baseline). Evidence: `evidence/live-t8b-savechanges-guard.md`.

      **T8b OUTCOME (spurt 7, cycle 7).** Landed exactly as specified.
      Guard live in `flexicon/code/FLExProject.py`'s `SaveChanges()`; all
      three docstring `Example` blocks corrected; all 11 C22 sites
      repaired (public-API pins re-pointed at `FP_TransactionError`,
      liblcm-mechanism pins P-7/P-8/P-9 switched to the raw `usm.Save()`
      accessor); `test_transaction_honesty.py`'s slice widened (both
      `save_body` 1000->6000 AND `refresh_body` 2500->4000 -- see `spec.md`
      **C26** ADDENDUM, a second window the original enumeration missed).
      Probe file 10 -> 11 live tests (**P-11** added); `test_abort_session_live.py`
      12/12. Both `run_mode: live`; offline 1290 passed, deselected
      474 -> 475. **Headline: the full P-5/P-7/P-10-case-C sequence now
      re-measures 25/25 in memory and 25/25 on disk**, up from 0/25
      pre-guard -- C17's ceiling is met, by the only route C17 said could
      meet it. **P-11 finding (routed, not absorbed here):** an escaping
      `FP_TransactionError` inside `UndoableOperation()` did NOT discard
      the block's object creations (25/25 survived), contradicting that
      module's own rollback-discards-everything docstring claim; routed
      per `spec.md` **C25** (spurt 8) to `undoable_operation.py`'s
      docstring (`/lex-programmer`'s diff) plus a new "Awaiting user
      approval" QUEUE.md item for the broader question.
      Evidence: `evidence/live-t8b-savechanges-guard.md`.

**Checkpoint CP-D -- REACHED 2026-09-07 (spurt 7, cycle 7).** T8a and T8b
both landed and live-verified; the guard's shape (C21) is shipped with a
mode-differentiated message; all 11 C22 sites are accounted for with no
silently-broken pin (re-keyed against `/lex-lead`'s authoritative
enumeration as `spec.md` **C26**, spurt 8); P-11 is measured, not
inferred; the offline suite is green including the (doubly) widened
`test_transaction_honesty.py` slices. `spec.md` C21-C26 reflect the
shipped shape. T7 (Checkpoint 2c) is now IN PROGRESS per C23's recut.

---

## Checkpoint 3 -- P2: CHANGELOG entry (T5, now SPLIT into T5a / T5b)

**SPLIT 2026-09-07 (spurt 5) by `spec.md` C19.** "Defer all of T5" was
re-costed and found NOT to be neutral: `CHANGELOG.md` has a live
`[Unreleased]` section, and T3 is **already committed to `main` inside that
window with no entry at all**. If a version were cut today, consumers would
get a behaviour change to a shipped public method -- including C14's
observability regression -- entirely undocumented. So:

- **T5a -- minimal `[Unreleased]` stub. RULING-INDEPENDENT. RECOMMENDED.**
  Notes **T3 only**, scoped per C17's two halves: the P-3 path is fixed
  (0/25 -> 25/25); the `SaveChanges()`-at-depth>0 path is **NOT** fixed and
  `CloseProject()` currently **returns normally** there. That is a
  description of *shipped behaviour*, so it takes no position on the fourth
  ask, and it discloses nothing public issue #243 does not already state.
  **Churn cost is zero** -- it sits under `[Unreleased]`, so if T7 later
  flips that path to raise, the entry is edited before any version cut and
  nothing published ever churns. Constraints: C10 (no `.fwdata` claim), C14
  (loudness not data), C17 (state BOTH halves). Docs-only, live-exempt.
  **Offered as a second pre-authorised, ruling-independent unit, exactly as
  T6 was -- the USER greenlights it or not. Do not run it inside any loop.**
- **T5b -- the prominent P2 release note + the `TRANSACTION_GUIDE.md`
  corrections + Q4's placement/wording. Gate LIFTED 2026-09-07 (spurt 8,
  cycle 8):** the user's ruling landed as C20 (spurt 6) and the guard
  landed as T8b (spurt 7), so the wording this task depends on is now
  settled and measured, not merely proposed. Dispatched to `/lex-doc` this
  cycle IN PARALLEL with T7 (not strictly after it): the `SaveChanges()`
  docstring correction itself already shipped inside T8b's own diff (per
  the NARROWING below), so T5b's remaining surface (CHANGELOG,
  `docs/TRANSACTION_GUIDE.md`, Q4) does not depend on T7's specific log
  wording landing first -- only on T8b, which is done. The T5 task text
  below is T5b's.

**RE-GATED 2026-09-07 (spurt 4): T5 is now LAST, after T6 and T7.** It was
originally third of three; the CP-B ruling inserted Checkpoint 2c ahead of
it. T5 cannot be written before T7 lands and before the user rules, because
its wording depends on both. Two hard constraints on that wording, on top of
Q4:

- **It must NOT claim #243 fixes the owner's filed incident.** Per C9 the
  incident is the P-5 -> P-3 chain, and P-5 still measures 0/25 (C13).
  #243 fixes the P-3 loss mechanism (25/25) and, via T7, makes the remaining
  loss impossible to miss -- it does not make the owner's sequence save.
- **It must not overstate T7 either.** C14: the remedy restores LOUDNESS,
  not DATA. Same discipline as C10's ban on claiming the `.fwdata` swap is
  fixed.

- [~] **T5** (DOCS-ONLY, EXEMPT FROM LIVE VERIFICATION) **IN PROGRESS
      (spurt 8, cycle 8) -- dispatched to `/lex-doc` this cycle, in
      parallel with T7 at `/lex-programmer`. See
      `specs/243-closeproject-save-guard/reviews/cycle8-doc.md` for what
      landed this pass; leave the checkbox open until `/lex-lead`
      verifies it, per this feature's own "not taken on report"
      discipline.** NARROWED 2026-09-07 (spurt 7, cycle 7) by `spec.md`
      C21/C23. The three
      shipped docstring `Example` corrections (`SaveChanges()`,
      `RefreshFromDisk()`, `AbortSession()`'s `else:` branch) that used to
      live under this task's "ADDED by the C9 ruling" heading below **MOVE
      TO T8b** -- they are guaranteed refusals under the now-implemented
      C21 guard, not merely a pre-existing docstring inaccuracy, so they
      ship in the same diff as the guard, not deferred here. What T5b
      (this task) keeps:
      - the prominent P2 release note (`CHANGELOG.md`, cross-referencing
        the `[4.4.0]` `undoable` default-flip entry, per C8);
      - **`docs/TRANSACTION_GUIDE.md`**, especially the "SaveChanges()
        Method" -> "Notes" section (`:154-183`), whose bullet "**No side
        effects on transactions**: calling `SaveChanges()` does NOT affect
        the undo stack or active transactions" (`:181`) is the precise
        inverse of the measured truth (P-5/P-7/P-10: it can collapse the
        session envelope and, post-guard, refuses outright at depth > 0).
        The two `SaveChanges()` usage examples at `:43-50` and `:170-176`
        also need review against the new guard (both are written using
        `Transaction()`, so they are `undoable=True`-default-safe today,
        but the doc never states that the same code under `undoable=False`
        now raises `FP_TransactionError`);
      - Q4's placement/wording answer (`/lex-doc`'s call, per C8).
      Dispatch `/lex-doc` with this spec (`spec.md` sections 3, C8, Q4, C21,
      C23), the `[4.4.0]` `CHANGELOG.md` entry, and `docs/TRANSACTION_GUIDE.md`
      so it can draft the release note and correct the guide -- per the
      Archivist/Doc-Agent division of labour (C8), the Archivist does not
      author the entry's prose itself. Stage and commit `/lex-doc`'s
      returned patch. **CHANGELOG classification note:** `SaveChanges()`
      changing its raised exception type (liblcm `InvalidOperationException`
      -> `FP_TransactionError`) at `CurrentDepth > 0` is a **public-behaviour
      change**, not merely a fix -- the CHANGELOG must classify it under a
      heading that says so (e.g. `Changed` / `Breaking`, per the project's
      own Doc-Agent classification discipline), not bury it under `Fixed`
      alongside T3's P-3 guard. This task is docs-only and carries NO
      live-verification requirement -- no `target_sandbox`, no evidence
      file, no pytest invocation.

      **P2 must NOT claim the fix prevents the `.fwdata` file replacement**
      (C10) -- it fixes the loss of the in-memory session only.

      **Historical text retained below for the record -- SUPERSEDED by the
      narrowing above; the docstring correction it describes now ships in
      T8b, not here:**

      Correct the `SaveChanges()` docstring at
      `flexicon/code/FLExProject.py:563-588`. Its Example block currently
      shows `with project.Transaction("import batch"): ...` followed by
      `project.SaveChanges()`, which is correct under `undoable=True`
      (depth 0 inside `Transaction()`) but a GUARANTEED
      `InvalidOperationException: Commit at wrong place.` under
      `undoable=False` (depth 1 for the whole session, per the P-2 table)
      -- and that raise also collapses the session envelope. This shipped
      example is how the owner's incident was reachable without any exotic
      caller code (C9); the docstring's "the session stays open" note
      (line 572) is the same overclaim the probe disproved. The docstring
      must state that under `undoable=False` `SaveChanges()` must not be
      called while `HasOpenSessionTask()` is true, and point at
      `HasOpenSessionTask()` (T1).

**Checkpoint:** `CHANGELOG.md` updated and committed, acceptance criterion 5
in `spec.md` section 5 satisfied. All three surviving asks (P0, P1, P2) are
now landed with live evidence on file for P0/P1 and a docs commit for P2.
Feature-complete pending `/lex-lead`'s final sign-off and Q2/Q3's
disposition (Q1 is already CLOSED -- spec.md C9/C10). Q2 and Q3 may remain
open going into sign-off per `spec.md`'s instruction not to silently decide
them -- surface them explicitly in the handoff/report rather than closing
the feature silently around them.

**T7 and T5b LANDED at spurt 8 (cycle 8) -- see `STATUS.md`.** Both
checkpoints above are now satisfied in full. The cycle-8 QC audit (run by
`lex-verification`, substituting for the unregistered `lex-qc`, per
`spec.md` C28's gate note) then found two P1s on the shipped `SaveChanges()`
guard, neither blocking (P0 count 0), opening one more task below.

---

## Checkpoint CP-CLOSE -- T9: the fail-open catch's contract and coverage (spurt 9)

Opened by the cycle-8 QC audit's P1 #1, ruled as `spec.md` **C28**. This is
the ONLY task standing between item 1 and closure. `SaveChanges()`'s
fail-open catch (`FLExProject.py:845-856`) is NOT changed in shape or
policy -- C21's fail-open behaviour stands exactly as shipped. Touches
docs/comments in `flexicon/code/FLExProject.py` (T9a) and one new offline
test file (T9b) only; no other production code changes.

- [x] **T9a** (DOCS-ONLY, comment/docstring, zero executable change)
      Broaden the `SaveChanges()` docstring/inline comment around the
      `except Exception as e:` fail-open catch (`FLExProject.py:845-856`)
      so it states the ACTUAL contract instead of the narrower one C21
      documented: the catch is intentionally broad (any exception from the
      `CurrentDepth` read fails open, not only `FP_ProjectError`), and name
      the one case verified safe by code inspection --
      `ObjectRepository()` shares the identical `self.project` dependency
      and raises first on a closed/never-opened project, so `usm.Save()` is
      never reached either way. State the residual explicitly, per C28: if
      any OTHER exception can leave `ObjectRepository()`/`usm.Save()` both
      still reachable at `CurrentDepth > 0`, fail-open would proceed blind
      into #243's own incident, and no such state has been found or
      measured. Do not word this as "the branch is safe" -- only the one
      checked case is.
- [x] **T9b** (OFFLINE test, no live verification required -- this task
      adds coverage for a code path that does not depend on live LCM state
      beyond what existing doubles already provide) Add the one missing
      test: force the `CurrentDepth` read inside `SaveChanges()` to raise
      an exception OTHER than `FP_ProjectError` (e.g. patch/mock
      `ActionHandlerAccessor.CurrentDepth` to raise a generic `Exception`
      or a second, unrelated exception type) and assert `SaveChanges()`
      logs a WARNING and falls through to attempt `usm.Save()` rather than
      re-raising. Add to the existing offline suite (do not create a new
      live probe file); confirm zero live markers on the new test and that
      the full offline suite stays green plus this one addition.

**Checkpoint CP-CLOSE: REACHED AND PASSED (spurt 9, cycle 9).** T9a and
T9b both landed; offline suite **1292 passed / 475 deselected** including
the new test; live gate re-run green (probe 11/11, abort-session 12/12,
`run_mode: live`, `evidence/live-t9-failopen-coverage.md`); `spec.md`
C28/C29 on file, plus **C30** at closure. **`/lex-lead` signed item 1 off
as `feature_complete` (APPROVED) at cycle 9.** No task remains open on this
feature. T2 stays DROPPED (C12) -- do not re-tick it as open work.
GitHub #243 is deliberately left OPEN for the user's decision (C10's
unmeasured `.fwdata` half); the crew does not close issues.
