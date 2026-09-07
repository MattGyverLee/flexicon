# TASKS -- 243-closeproject-save-guard

Derived from `spec.md` sections 3 and 6 (C1-C10). Issue: #243.

**CHECKPOINT NUMBERING -- read this first.** The campaign
(`specs/tier1-silent-data-loss/QUEUE.md`) called the spec+probe milestone
"Checkpoint 1"; that milestone is DONE (spurt 1, 2026-09-07) and is NOT any
of the checkpoints below. The three checkpoints in this file are the
IMPLEMENTATION checkpoints and start after it. To remove the collision they
are referred to as **CP-A (T1-T2)**, **CP-B (T3-T4)** and **CP-C (T5)**;
the older "Checkpoint 1/2/3" headings below are retained only so existing
cross-references still resolve. The next spurt starts at **CP-A / T1**.

**Q1 is CLOSED (spec.md C9/C10, ruled 2026-09-07).** No task below may
reopen it, and no task may wait on owner repro steps -- the owner's
sequence is reconciled as a P-5 -> P-3 chain that the C6 guard breaks. Q2
and Q3 remain genuinely open and are decided at T3 and T1 respectively.

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

---

## Checkpoint 1 -- P1: the depth-read surface (T1-T2)

Prerequisite for everything else per C6. Touches
`flexicon/code/FLExProject.py` only.

- [ ] **T1** (LIVE) Add a private depth-read helper on `FLExProject` (e.g.
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
- [ ] **T2** (LIVE) Point the three existing internal lenient call sites
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

**Checkpoint:** T1 and T2 both green and evidence filed. `FLExProject` now
exposes `HasOpenSessionTask()`/`CurrentDepth` matching the frozen P-2 table
exactly, including both new closed/never-opened raise cases, and the three
pre-existing internal call sites are unchanged in behaviour. This is the
prerequisite C6 requires before the P0 guard (Checkpoint 2) may begin. Stop
here, update `STATUS.md` / `.crew-handoff.json`, commit.


---

## Checkpoint 2 -- P0: the CloseProject() End-guard and its regression tests (T3-T4)

Consumes T1's public surface per C6. Touches `flexicon/code/FLExProject.py`
only.

- [ ] **T3** (LIVE) Implement the C1/C6 guard around
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
- [ ] **T4** (LIVE) EXTEND the probe file's own regression tests to prove T3
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

**Checkpoint:** T3 landed, T4's extended P-3 and P-5 tests both green
against the patched `FLExProject.py`, `test_p1_mode_matrix` and
`test_p2_depth_table` (unaffected by T3) still green, `test_p4_control_run_normal_close`
still green. Full extended probe file run
(`python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s`)
shows all tests passing with `run_mode: live`. Update `STATUS.md` /
`.crew-handoff.json`, commit. Acceptance criteria 1, 2, 3, 4 in `spec.md`
section 5 are satisfied at this checkpoint.

---

## Checkpoint 3 -- P2: CHANGELOG entry (T5)

- [ ] **T5** (DOCS-ONLY, EXEMPT FROM LIVE VERIFICATION) Dispatch `/lex-doc`
      with this spec (`spec.md` sections 3, C8, Q4) and the `[4.4.0]`
      `CHANGELOG.md` entry for the `undoable` default flip, so it can draft
      a new, prominent CHANGELOG entry documenting this fix and
      cross-referencing the 4.4.0 entry -- per the Archivist/Doc-Agent
      division of labour (C8), the Archivist does not author the entry's
      prose itself. Stage and commit `/lex-doc`'s returned patch. This task
      is docs-only and carries NO live-verification requirement -- no
      `target_sandbox`, no evidence file, no pytest invocation.

      **ADDED by the C9 ruling (2026-09-07) -- also in P2's docs scope:**
      correct the `SaveChanges()` docstring at
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
      `HasOpenSessionTask()` (T1). **Docstring/prose only** -- changing
      `SaveChanges()`'s BEHAVIOUR is out of scope (spec.md section 4 binds
      this feature to the three asks) and is routed to QUEUE.md "Awaiting
      user approval". It stays live-exempt as a pure-docs change, but the
      diff must touch no executable line; if it does, it is no longer T5.

      **P2 must NOT claim the fix prevents the `.fwdata` file replacement**
      (C10) -- it fixes the loss of the in-memory session only.

**Checkpoint:** `CHANGELOG.md` updated and committed, acceptance criterion 5
in `spec.md` section 5 satisfied. All three surviving asks (P0, P1, P2) are
now landed with live evidence on file for P0/P1 and a docs commit for P2.
Feature-complete pending `/lex-lead`'s final sign-off and Q2/Q3's
disposition (Q1 is already CLOSED -- spec.md C9/C10). Q2 and Q3 may remain
open going into sign-off per `spec.md`'s instruction not to silently decide
them -- surface them explicitly in the handoff/report rather than closing
the feature silently around them.
