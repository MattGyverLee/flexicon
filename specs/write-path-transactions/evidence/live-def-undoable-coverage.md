# Live evidence — DEF-COV + B2t: `undoable=True` coverage

Task: **DEF-COV** (live `undoable=True` coverage, the blocker D9 recorded
against DEF) and **B2t** (end-to-end persistence test from issue #237).

Date: 2026-08-16
Branch: `write-path-transactions-b1-b3`
Artifact under test: `tests/operations/test_undoable_mode_live.py` (33 tests),
plus the new `target_sandbox_path` fixture in `tests/conftest.py`.

---

## 1. Why this run exists

D9 (recorded during A3's live verification) established that the
`undoable=True` path had **never** been exercised against a live LCM. Every
landed live suite used the `target_sandbox` fixture, which opens
`undoable=False`. B1 and B2 had therefore been marked complete, *for the mode
they exist to serve*, on offline-double evidence alone — and those doubles had
encoded the bug: they modelled `RollBack` as an assignable attribute, so 30
offline tests passed against code that silently discarded every write when
run live.

The D9 fix was a point fix. This is the coverage, and it is the gate on DEF.

---

## 2. Exact commands

Coverage suite:

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_undoable_mode_live.py -m requires_live_project -q -p no:randomly
```

Result: **33 passed, 1 warning in 19.43s**
(the one warning is the pre-existing `flexlibs2` -> `flexicon` rename
DeprecationWarning from `tests/conftest.py:140`, unrelated to this work)

`tests/live_status.json` after the run:

```json
"run_mode": "live",
"run_timestamp": "2026-08-16T07:56:30Z"
```

Not `"mock"` — the run reached a real LCM. `FLEXLIBS_REQUIRE_LIVE=1` was set,
so a fallback to mocks, a locked project or a missing fixture would have been
a hard failure rather than a silent skip.

All 33 tests run against a tempdir copy of `tests/fixtures/Target 2026-07-06
0218.fwbackup`. The user's real Target project is never opened.

---

## 3. Pre-state and post-state, read back from the LCM

Captured with a temporary harness driving the same fixtures and the same
public API, then removed. Every value below is **re-queried through the
Operations layer** after the write, never asserted from the value passed in.
Session 2 is a brand-new `FLExProject` on the same file, so nothing survives
into it except what actually reached disk.

```
SESSION 1 (writeEnabled=True, undoable=True)
  PRE  LexEntry.Find(form)                             = None
  PRE  ActionHandlerAccessor.CurrentDepth              = 0
  PRE  ActionHandlerAccessor.CanUndo()                 = False
  IN   CurrentDepth (inside block)                     = 1
  POST CurrentDepth (after block)                      = 0
  POST ActionHandlerAccessor.CanUndo()                 = True
  POST ActionHandlerAccessor.GetUndoText()             = 'TEST_evidence write'
  POST LexEntry.Find(form) is not None                 = True
  POST Senses.GetGloss(...) re-read                    = [None, 'TEST_gloss two']
  IN   LexEntry.Find(dropped) before raise             = True
  POST LexEntry.Find(dropped) after rollback           = None
  POST LexEntry.Find(bare) [per-operation UoW]         = True
  --- CloseProject() ---
SESSION 2 (reopened, writeEnabled=False) -- disk state
  REOPEN LexEntry.Find(form) is not None               = True
  REOPEN Senses.GetGloss(...) re-read                  = [None, 'TEST_gloss two']
  REOPEN LexEntry.Find(dropped)                        = None
  REOPEN LexEntry.Find(bare) is not None               = True
  REOPEN ActionHandlerAccessor.CanUndo()               = False
```

What each line settles:

| Reading | Settles |
|---|---|
| `CurrentDepth` 0 -> 1 -> 0 | No session envelope in this mode; the block opens and closes exactly one UoW and leaks nothing (#234's shape) |
| `CanUndo()` False -> True | The clean block **committed**. Under D9 this stayed False — the machine-checkable signature of the bug |
| `GetUndoText() == 'TEST_evidence write'` | Label fidelity: the caller's label reaches the FLEx Ctrl+Z menu (D5 rationale #2, verified live for the first time) |
| `REOPEN Find(form)` True, gloss on disk | **Issue #237 is closed.** The write survived `CloseProject()` and a fresh open |
| `REOPEN Find(dropped)` None | The rollback is **durable**, not merely a cache clear — a rolled-back object does not reappear |
| `REOPEN Find(bare)` True | The `per-operation-uow` capability holds end to end, with no explicit block. This is the shape FlexToolsMCP generates |
| `REOPEN CanUndo()` False | Live evidence for CO1's in-process-only scope caveat on #235 |

(`[None, 'TEST_gloss two']` — the `None` is the auto-created blank sense from
`LexEntry.Create(..., create_blank_sense=True)`; the second is the sense this
harness created and then re-glossed.)

---

## 4. The suite is validated by mutation, not by passing

A suite that passes proves little here — the suite that **missed** D9 also
passed. So the coverage claim is stated as a mutation result.

D9 was reintroduced by reverting both call sites to the assignment form
(`self._helper.set_RollBack(exc_type is not None)` ->
`self._helper.RollBack = (exc_type is not None)`) in
`flexicon/code/transaction.py` and `flexicon/code/undoable_operation.py`, and
both suites were re-run.

| Suite | With D9 reintroduced |
|---|---|
| `tests/operations/test_undoable_mode_live.py` (new) | **19 failed, 14 passed** |
| `tests/write_path_transactions/` + `test_b1t_action_handler_double.py` (offline, as it stands today) | **14 failed, 42 passed** |

Failing groups in the live suite: `TestCleanBlockCommits`,
`TestPerOperationUnitOfWork`, `TestNestingLive`, `TestUndoRedoLive`,
`TestBracketsAcrossDomains`, `TestPersistenceAcrossReopen`.

**A correction worth recording, because the first draft of this file got it
wrong.** The offline suite was expected to stay green under the mutation, on
the strength of D9's account that "the doubles encoded the bug". It does not:
it fails 14. The reason is that D9's fix did not stop at the two call sites —
it also hardened both doubles to raise on the assignment form and added a
source-level guard. So the offline suite that missed D9 no longer exists; the
one in the tree today catches it.

That makes the honest comparison a historical one rather than a live A/B:

- The offline suite **as it stood before the D9 fix** passed 30/30 against
  code that discarded every write live. That is the documented failure.
- The offline suite **today** catches the mutation, but only via the
  double-level and source-level guards — i.e. by asserting *how the code
  calls pythonnet*, not by observing that data survived. That is a
  necessary guard and a real improvement, and it is still not coverage:
  it would not catch a different mechanism with the same effect.
- The live suite catches the mutation by observing **data loss**, including
  across a `CloseProject()` boundary, which no offline double can do.

The 14 live tests that still passed under the mutation remain the useful
diagnosis, and are recorded as **D10**: they are largely the tests asserting
that a rollback *happened*, which a build that rolls back everything
satisfies perfectly. That is the shape B1t was mostly built out of. Under
`undoable=True` the **commit** path is the one carrying a silent
total-data-loss mode, so it needs the stronger test — and at least one test
must survive `CloseProject()`, because an in-memory assertion cannot
distinguish "written" from "written and then discarded".

Both files were restored from git (`git checkout --`) immediately after the
mutation run, and the suite re-verified green.

---

## 5. Claims covered

| # | Claim | Covered by |
|---|---|---|
| 1 | A clean block COMMITS | `TestCleanBlockCommits` (2) |
| 2 | An exception ROLLS BACK, for real | `TestExceptionRollsBackLive` (5) |
| 3 | Each operation is its own UoW | `TestPerOperationUnitOfWork` (4) |
| 4 | Nesting joins, never re-opens | `TestNestingLive` (4) |
| 5 | Undo/Redo drive the live stack (B3) | `TestUndoRedoLive` (4) |
| 6 | The 295 B2 brackets work in *this* mode | `TestBracketsAcrossDomains` (4) |
| 7 | Writes survive close and reopen (#237, B2t) | `TestPersistenceAcrossReopen` (4) |
| 8 | D9 cannot silently return | `TestD9RollBackRegression` (1) |
| — | Mode guards (D8), fixture is live and from this checkout | `TestUndoableModeGuards` (2), `TestUndoableFixtureReachesLiveLCM` (3) |

Claim 6 samples domains rather than exhausting all 295 sites, and
deliberately avoids the Notebook, Etymology and Example methods this
feature's concerns record as pre-existing-broken on any live project — those
fail *before* the bracket is entered, so they cannot say anything about
bracket behavior in either mode. **This is a stated coverage limit, not a
silent one:** the bracket sweep's per-site correctness rests on the B2g
scanner plus batches 8-11's `undoable=False` live runs; what this file adds
is that the bracket *mechanism* behaves correctly under `undoable=True`.

---

## 6. Semantics discovered and now documented

`test_inner_exception_caught_inside_the_outer_block_still_commits` pins a
consequence of B1's join-don't-reopen rule that had not been written down:
because a nested block joins the enclosing UoW, it has **no independent
rollback**. Catching an inner exception inside an outer block therefore
commits the inner's partial writes.

This is not a defect — opening a real nested unit is exactly what liblcm
punishes (`UndoStack.cs:209-216` rolls the already-open unit back, then
throws). But it is a semantic callers must be told rather than discover, so
it is now documented in `docs/EXCEPTION_HANDLING.md` ("Atomicity Under
`undoable=True`: the Block Is the Unit") and flagged in
`docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`'s migration path.

---

## 7. Verdict

**PASS — verified live.**

- `run_mode: "live"`, `FLEXLIBS_REQUIRE_LIVE=1`, 33/33 passed.
- Pre/post state read back from the LCM, including across a
  `CloseProject()` / reopen boundary.
- Reintroducing D9 turns 19 of the 33 red, on observed data loss rather than
  on call-shape assertions (see §4 for the corrected offline comparison).

### Other suites run

| Suite | Result |
|---|---|
| `tests/operations/test_abort_session_live.py` (A3) | 12 passed |
| `tests/operations/test_grammar_brackets_live.py` (B2 batch 10) | 16 passed |
| `tests/operations/test_lexicon_brackets_live.py` (B2 batch 11) | 20 passed, 3 xfailed (the recorded pre-existing Lexicon bugs) |
| `test_allomorphs/etymologies/examples_live.py` | 18 passed |
| `test_locations/persons/pronunciations/variants_live.py` | 27 passed, 3 skipped |
| `tests/write_path_transactions/` + `test_b1t_action_handler_double.py` (offline) | 56 passed |

**A note on the full live sweep, which was NOT run and should not be.**
Attempting `pytest tests/operations/ -m requires_live_project` stalls
indefinitely. The cause is pre-existing and unrelated to this work: around 25
files in that directory (e.g. `test_pos_operations.py:487`) define their own
fixture that calls `AllProjectNames()[0]` and opens the first real project on
the machine **in place, write-enabled**. That is precisely the hazard
CLAUDE.md warns about ("Never run bare `pytest` ... both collect and EXECUTE
the ~322 `requires_live_project` tests in-place against real projects"). The
supported gate is per-file, which is what the table above reports. Worth
filing separately: those fixtures should move to `target_sandbox`.

**Consequence for DEF:** the coverage blocker recorded in this feature's
concerns is **discharged**. DEF remains `needs_human` — it is a public-API
default change, and that decision is the maintainer's, not a missing test.
