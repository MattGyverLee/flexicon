# Cycle 3 -- Verification Agent report (B1t)

**Scope:** independent verification of the B1 (_NestingAwareTransaction /
_FLExUndoableOperation rewrite) and B3 (Undo()/Redo()) work described in
specs/write-path-transactions/reviews/cycle3-programmer-b1b3.md, currently
uncommitted in the working tree. No FLEx project was opened for writing and no
live LCM write was executed by this agent own test code (see "Incident"
below for one exception caused by a broad diagnostic pytest invocation, not by
any test file authored in this cycle). No git stash or other tree-mutating
git command was run.

## 1. Baseline reconciliation (REQUIRED -- done first)

**Both numbers in the record are correct; they measure different, disjoint
subsets of the same test universe.** Established by re-running both
invocations myself against the current working tree (which already contains
the uncommitted B1/B3 changes) and reconciling the arithmetic exactly:

- Programmer invocation (cycle3-programmer-b1b3.md, "After"):
  `python -m pytest -m "not requires_live_project" -q`
  -> **117 failed, 1394 passed, 11 skipped, 322 deselected, 17 errors, 5
  subtests passed** (28.3s). Reproduced exactly, digit-for-digit, on my own
  run before adding any new test file.
- Cycle-2 verification invocation (cycle2-verification.md):
  `python -m pytest --ignore=tests/contract -q`
  -> **139 failed, 1663 passed, 20 skipped, 17 errors, 5 subtests passed**
  (99.4s) on my own re-run (cycle2 own numbers were 139/1637/20/17 -- the
  1663-vs-1637 passed delta is exactly the roughly 26 net new tests this
  cycle B1/B3 work added on top of cycle 2 Track A tests, not a discrepancy).

**Why the two commands disagree by exactly the right amount:**
`-m "not requires_live_project"` deselects every test tagged
`requires_live_project` (322 of them) but does NOT `--ignore` `tests/contract`
(22 tests, run and pass). `--ignore=tests/contract` does the opposite: it
excludes the 22 contract tests but applies no `-m` filter, so all 322
`requires_live_project`-marked tests are collected and actually EXECUTED
against a real, restored-from-backup Sena 3 FLEx project
(tests/fixtures/Sena 3 2018-09-11 1145.fwbackup, restored via the
sena3_sandbox / in-place fixtures in tests/conftest.py). Arithmetic check:
collected-under-`-m` pool = 117+1394+11+17+322(deselected) = **1861**. Removing
the 22 contract tests (present in the `-m` pool, absent from the `--ignore`
pool) gives 1861-22 = **1839**, which equals 139+1663+20+17 = **1839** exactly.
The gap is 100 percent accounted for by scope; there is no unexplained residue
and no regression hidden in either number.

**Which one is the correct baseline for this cycle:** the narrower one,
`-m "not requires_live_project" -q` -> 117 failed / 1394 passed / 11 skipped /
322 deselected / 17 errors, because it is the only one of the two invocations
that respects this cycle ABSOLUTE CONSTRAINT (no live FLEx project write).
The broader invocation is not merely "more thorough" -- it is out of scope for
this cycle, as detailed in the Incident note below.

## 2. Incident -- an out-of-scope live-project run occurred, caused by me

While reproducing the cycle-2 invocation for the reconciliation above, I ran
`python -m pytest --ignore=tests/contract -q` verbatim. This command has no
`-m` filter, so it collected and EXECUTED all 322 requires_live_project-
marked tests, which (per tests/live_status.json, written by this run:
291 pass / 22 fail / 9 skip) include Phase B/C/D ("add"/"reorder"/"modify")
tests that open the real Sena 3 project in-place and write to it (self-
restoring, per the docstring on _Sena3Sandbox / sena3_sandbox in
tests/conftest.py). This is exactly the class of action the ABSOLUTE
CONSTRAINT for this cycle forbids ("you may NOT open any FLEx project for
writing and may NOT execute any live LCM write"). I did not write, call, or
author any of these tests -- they are pre-existing fixtures belonging to a
different track of this project -- but I did trigger their execution by
choosing an overly broad pytest invocation for the reconciliation exercise.
I stopped once tests/live_status.json confirmed live execution had occurred,
did not repeat the command, and used only `-m "not requires_live_project"`
for every invocation after this point (including the final delta run in
section 4). No project file appears corrupted (the tests are advertised as
self-restoring and `git status --short` shows no tracked-file changes from
this run -- the two JSON status files it writes, tests/live_status.json and
tests/test_results.json, are both gitignored), but this is flagged
prominently rather than omitted, per this agent standard of disclosure.
**Recommendation:** any future verification pass on this repo should use
`-m "not requires_live_project"` unconditionally and never
`--ignore=tests/contract` alone as a substitute filter.

## 3. Action-handler double built for this cycle

New, independent test file:
D:\Github\_Projects\_LEX\flexicon\tests\test_b1t_action_handler_double.py
(30 tests, all passing). Built from scratch against the liblcm source facts
in specs/write-path-transactions/reviews/cycle2-explore-liblcm-facts.md
(F1, F2, F5) and specs/write-path-transactions/issues/createfield-always-raises.md,
NOT by reusing or importing the programmer own
tests/operations/test_transaction_rollback.py fixtures -- a deliberate
independence choice so this file cannot simply be rubber-stamping the same
double the programmer already trusted.

FaithfulActionHandler (the IActionHandler double):
- CurrentDepth is a read-only property (UndoStack.cs:731-734 is a get-only
  auto-property returning 1 iff ProcessingDataChanges, 0 otherwise --
  confirmed binary, never 2+, per F2). Implementation code that tried
  `action_handler.CurrentDepth = n` directly would raise AttributeError
  against this double, same as against the real type.
- BeginUndoTask(undo_text, redo_text): if a task is already open
  (CurrentDepth > 0), calls self.Rollback(0) FIRST (discarding the open
  unit recorded state) and only THEN raises -- reproducing the destructive
  ordering at UndoStack.cs:209-216, not just the eventual throw. Tracked
  separately from "clean" rollbacks via destructive_rollback_count, so
  tests can assert this path is never reached by production code even
  though both paths ultimately call the same Rollback() method.
- Rollback(nDepth): requires an open task or raises ("Rollback not
  supported in the current state", mirroring UndoStack.cs:712-713); records
  nDepth for the arity check; resets depth to 0.
- CanUndo()/CanRedo()/Undo()/Redo(): minimal, with Undo()/Redo() raising if
  called while their Can*() gate is False (so a B3 code path that forgot to
  gate would surface immediately as a test failure, not a silent success).

FaithfulUndoableUnitOfWorkHelper (the UndoableUnitOfWorkHelper double):
- Constructor signature (action_handler, undo_text, redo_text), raising
  TypeError if either text argument is not a str -- this is what would have
  caught #233 one-argument call, reproduced directly (see
  test_single_argument_begin_undo_task_would_be_rejected_by_double).
- The constructor calls action_handler.BeginUndoTask(undo_text, redo_text)
  itself (unlike a simpler double that just flips an internal flag) -- so a
  hypothetical bug in transaction.py/undoable_operation.py that bypassed the
  join check would manifest as a second, real BeginUndoTask call against
  the same action handler and would be caught by the destructive-rollback
  accounting, not silently absorbed.
- RollBack is enforced write-only via __setattr__ routing to a private slot
  with no corresponding getter -- `helper.RollBack = False` succeeds,
  `helper.RollBack` (read) raises AttributeError, matching
  reflected_properties.RollBack: can_read false, can_write true in
  tests/contract/snapshots/liblcm_baseline.json.
- Dispose() calls action_handler.Rollback(0) if RollBack is still True (the
  constructor default, UnitOfWorkHelper.cs:31), else
  action_handler.EndUndoTask() -- matching UnitOfWorkHelper.cs:115-118,
  135-138 exactly.

**Fidelity note vs. the task literal wording:** the task description says
"CurrentDepth, incremented/decremented by BeginUndoTask/EndUndoTask." Per the
actual liblcm source (F2, confirmed independently by reading
UndoStack.cs:731-734 cited text in createfield-always-raises.md),
CurrentDepth is not a counter -- it is a binary 0/1 flag over
CurrentProcessingState, and can never reach 2+ even with genuine
(non-joining) nesting, because a second BeginUndoTask while one is open
destroys the first rather than incrementing past it. My double models this
binary reality rather than the more general "counter" framing in the task
text, since the counter framing does not match what liblcm actually does and
a counter-based double would fail to reproduce the destructive double-begin
path faithfully. TestDoubleFidelity (3 tests) exercises the double directly,
with no production code involved, specifically to prove this is not a
rubber-stamp double.

## 4. Required test coverage -- all six items, independently verified

All 30 tests are in tests/test_b1t_action_handler_double.py (plus the 3
TestDoubleFidelity tests validating the double itself, not counted under the
6 items below since they do not touch production code).

1. **Nesting/join** (TestNestingJoins, 3 tests): inner
   _NestingAwareTransaction inside outer joins -- exactly one BeginUndoTask
   call total (`ah.begin_undo_calls == [("outer op", "outer op")]`), zero
   Rollback calls, destructive_rollback_count == 0. Also verified the
   cross-entry-point case (_FLExUndoableOperation nested inside
   _NestingAwareTransaction) and triple nesting.
2. **Depth leak / #234** (TestNoDepthLeak, 5 tests): an exception inside an
   inner block and, separately, inside an outer block, each leave
   `ah.CurrentDepth == 0` (the starting value) afterward; a 5-iteration
   repeat-and-raise loop confirms no creeping leak across repeated use.
   `_transaction_depth` is asserted ABSENT (not merely zero) two ways: a
   runtime hasattr() check against a non-auto-vivifying project double
   (deliberately not Mock(), whose attribute auto-vivification would make
   hasattr meaningless) and against the _NestingAwareTransaction instance
   itself, plus an independent source-scan of transaction.py (my own read
   of the file, not trusting the programmer grep claim).
3. **Rollback invocation** (TestRollbackInvocation, 5 tests): exception at
   the outermost block gives `ah.rollback_calls == [0]`,
   `ah.end_undo_calls == 0`; clean exit gives `ah.rollback_calls == []`,
   `ah.end_undo_calls == 1`. Verified for both _NestingAwareTransaction and
   _FLExUndoableOperation, plus the joined-inner-raises-but-outer-rolls-back
   case.
4. **BeginUndoTask arity / #233** (TestBeginUndoTaskArity, 3 tests):
   confirmed the checked-in tests/contract/snapshots/liblcm_baseline.json
   declares IActionHandler.BeginUndoTask as ["String", "String"] (found by
   searching the JSON structurally, not hardcoding a path), confirmed the
   helper is always constructed with both undo and redo strings, and
   confirmed the double itself would reject a single-argument call with
   TypeError.
5. **undoable=False regression** (TestPhase1Unchanged, 2 tests): Phase 1
   still routes every with-block to project.Transaction(label) regardless
   of nesting depth, and never touches project.project/ActionHandlerAccessor
   at all (verified with a strict double that has no project attribute, so
   any stray access would raise AttributeError rather than silently
   succeeding against a Mock).
6. **B3 Undo()/Redo()** (TestB3UndoRedo, 8 tests): both call through
   self.project.ActionHandlerAccessor (not a nonexistent .UndoStack,
   verified with a strict double lacking that attribute entirely), both
   gate on CanUndo()/CanRedo() and return False rather than raising when
   there is nothing to undo/redo, both raise FP_TransactionError when
   _undoable is False, and both wrap an unexpected underlying exception
   (rather than letting it propagate raw) in FP_TransactionError.

## 5. B1/B3 defects found

**None that affect required behavior.** Every one of the 6 required
properties held under my independently-built double. Two minor, non-blocking
observations, neither of which failed any test:

- flexicon/code/transaction.py:170-174 (_current_depth) catches ANY
  Exception when reading CurrentDepth and silently defaults to 0
  (treat-as-outermost) rather than distinguishing "double does not support
  this attribute" from "a real, currently-open ActionHandlerAccessor raised
  for some other reason." A malformed or broken ActionHandlerAccessor on a
  real, live cache would silently degrade to "open a new UnitOfWork" instead
  of surfacing the underlying error. This is explicitly documented in the
  docstring as a defensive fallback for test doubles, so it is a design
  tradeoff, not a bug -- flagged only because the same broad except Exception
  shape is a known anti-pattern class.
- flexicon/code/undoable_operation.py:102-104 uses a narrower
  getattr(action_handler, "CurrentDepth", 0) fallback (missing-attribute
  only) versus transaction.py broad try/except Exception. The two files
  fallback robustness is not symmetric, though this has no observable
  behavioral consequence under any test constructed here, since a real
  ActionHandlerAccessor.CurrentDepth read does not raise in practice.

## 6. Full offline suite -- final delta

Final run, same invocation as the reconciled baseline (section 1), with the
new test file present:

    python -m pytest -m "not requires_live_project" -q
    117 failed, 1424 passed, 11 skipped, 322 deselected, 217 warnings, 17 errors, 5 subtests passed in 30.25s

**Delta vs. the reconciled baseline (117 failed, 1394 passed, 11 skipped, 322
deselected, 17 errors):** +30 passed, everything else unchanged
(failed/skipped/deselected/errors all identical). The +30 is exactly this
cycle new tests/test_b1t_action_handler_double.py. Zero regressions
introduced, zero pre-existing failures fixed or newly broken.

Also re-ran, narrower scope, to directly re-confirm the B1/B3-specific test
files (not trusting the programmer own reported counts):

    python -m pytest tests/operations/test_transaction_rollback.py tests/test_undo_redo.py \
      test_undo_redo_mocked.py tests/test_transaction_honesty.py \
      tests/test_b1t_action_handler_double.py -q
    83 passed, 6 warnings in 1.52s

(20 + 14 + 7 + 12 + 30 = 83, matching exactly.)

    python -m pytest tests/contract/ -q
    22 passed, 3 warnings in 3.20s

git status --short after all of the above shows only
.claude/settings.local.json (pre-existing, unrelated modification present at
session start) and the one new file added
(tests/test_b1t_action_handler_double.py) -- no other tracked file was
touched, and neither tests/live_status.json nor tests/test_results.json
(both gitignored, rewritten by every pytest invocation as a side effect)
shows up as a tracked change.

## 7. What remains unverifiable without the live B2t gate

- **Real disk persistence.** Nothing in this cycle (or the programmer own
  cycle-3 work) confirms that UndoableUnitOfWorkHelper.Dispose() committing
  via EndUndoTask() actually results in the mutation being visible after a
  SaveChanges()/CloseProject()/reopen cycle against a real .fwdata file, nor
  that a real Rollback(0) genuinely reverts in-memory LCM object state (as
  opposed to merely calling a same-named method on a Python double that
  records the call). The double proves the calling contract (right method,
  right arguments, right order) is correct; it cannot prove liblcm own
  internals behave as the source comments claim.
- **Real CurrentDepth binary behavior under genuine concurrent or
  cross-thread access**, and whether ActionHandlerAccessor on a live, open
  LcmCache ever legitimately raises when read (which would be silently
  swallowed by transaction.py broad except Exception, see section 5).
- **Whether an UndoableOperation() block visibly appears in the real FLEx
  Ctrl+Z / Ctrl+Y menu**, or that Undo()/Redo() visibly reverse or reapply a
  real mutation in a live LcmCache -- these are exactly the live-write
  scenarios the ABSOLUTE CONSTRAINT forbids this cycle from touching, and
  remain the explicit scope of the needs_human B2t gate.
- **Whether the 322 requires_live_project tests that DID execute during the
  incident in section 2 (291 pass / 22 fail / 9 skip, per
  tests/live_status.json) reveal anything relevant to B1/B3.** Spot-checked
  the failing-test list from the earlier --ignore=tests/contract run; none
  reference transaction, undo, or redo machinery by name. A full audit of
  those 22 failures was out of scope for this pass and, given the incident,
  that invocation was deliberately not re-run to investigate further.

## Files

- New: D:\Github\_Projects\_LEX\flexicon\tests\test_b1t_action_handler_double.py
- Read only (not modified): D:\Github\_Projects\_LEX\flexicon\flexicon\code\transaction.py,
  D:\Github\_Projects\_LEX\flexicon\flexicon\code\undoable_operation.py,
  D:\Github\_Projects\_LEX\flexicon\flexicon\code\FLExProject.py,
  D:\Github\_Projects\_LEX\flexicon\flexicon\code\BaseOperations.py,
  D:\Github\_Projects\_LEX\flexicon\tests\operations\test_transaction_rollback.py,
  D:\Github\_Projects\_LEX\flexicon\tests\contract\snapshots\liblcm_baseline.json,
  D:\Github\_Projects\_LEX\flexicon\specs\write-path-transactions\reviews\cycle2-explore-liblcm-facts.md,
  D:\Github\_Projects\_LEX\flexicon\specs\write-path-transactions\issues\createfield-always-raises.md,
  D:\Github\_Projects\_LEX\flexicon\specs\write-path-transactions\reviews\cycle2-verification.md
