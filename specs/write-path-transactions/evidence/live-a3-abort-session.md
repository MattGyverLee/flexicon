# Live LCM evidence — A3 `FLExProject.AbortSession()`

Task: **A3** (`specs/write-path-transactions/tasks.md`, Checkpoint 3).
Date: 2026-08-16. Project: **Target** (tempdir sandbox restored from
`tests/fixtures/Target*.fwbackup`; the user's real Target was never opened).

Sandboxes are mandatory here, not a preference: `Rollback(0)` discards the
**whole** open unit of work, and under `undoable=False` that unit is the
entire session.

---

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
$env:PYTHONUTF8 = "1"
python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project -q
```

**Result: `12 passed`.**
`tests/live_status.json` → `"run_mode": "live"` (not `"mock"`).

Regression re-run of the previously landed live suites, after the B1 fix
below touched shared code:

```
python -m pytest tests/operations/test_grammar_brackets_live.py \
                 tests/operations/test_lexicon_brackets_live.py \
                 tests/operations/test_target_live_smoke.py \
                 -m requires_live_project -q
```

**Result: `39 passed, 3 xfailed`** — identical to the batch-10/11 baseline;
the 3 xfails are the documented pre-existing Lexicon bugs.

Offline gate: `python -m pytest tests/ -m "not requires_live_project" -q` →
**`35 failed, 1223 passed`**. The 35 are the known pre-existing set (#240
rename path, sync engine); passed count moves 1201 → 1207 (B4) → 1221 (A3
offline) → 1223 (the two added B1 regression guards). Zero regressions.

---

## Part 1 — A3 behaviour verified

Every assertion below re-queries the LCM after the write. Nothing asserts on
a value that was merely passed in.

| Claim | Pre-state (read from LCM) | Action | Post-state (re-read from LCM) |
|---|---|---|---|
| Rollback reverts **data**, not just undo records | `POS.Find("TEST_abort_me")` → object | `AbortSession()` → `True` | `POS.Find("TEST_abort_me")` → `None` |
| Reverts a modification to a **pre-existing** (on-disk) object | POS[0] name = `<original>`; renamed to `TEST_renamed_then_aborted`, re-read confirms rename | `AbortSession()` → `True` | `Find(<original>)` → object; `Find("TEST_renamed_then_aborted")` → `None` |
| **O2 catch** — envelope reopened | `CurrentDepth == 1` | `AbortSession()` | `CurrentDepth == 1` (would be `0` if the reopen were missing) |
| Session still writable after abort | — | abort, then `POS.Create` + `SetName` | both round-trip; FSM healthy |
| Non-terminal / repeatable | — | 3× create → abort | each returns `True`, each create gone, `CurrentDepth == 1` each time |
| Does not touch pre-session data | 5 pre-existing POS | create + `AbortSession()` | same 5 POS, by name; the new one gone |
| `undoable=True`, nothing open | `CurrentDepth == 0` | `AbortSession()` | returns `False`; no `Rollback` call |
| `undoable=True`, inside a block | `CurrentDepth == 1` | `AbortSession()` | raises `FP_TransactionError`; block then exits cleanly and **its write survives** — the refusal did not disturb the helper's unit |

**PASS** — A3 behaves as specified, including the O2 catch.

---

## Part 2 — CRITICAL pre-existing defect found and FIXED: B1 rolled back
every clean UnitOfWork under `undoable=True`

Surfaced while verifying A3's `undoable=True` path. **Not caused by A3.**

### Symptom

Under `undoable=True`, every write was silently discarded. `POS.Create`
returned an object whose `.Hvo` then raised `System.NullReferenceException`;
the POS count went 5 → 6 → back to 5; `CanUndo()` was `False` and
`UndoableActionCount` `0` after a clean block.

### Root cause

`UnitOfWorkHelper.RollBack` is `{private get; set; }` in C#. **pythonnet does
not synthesize a Python property when the getter is private** — it exposes
only the raw `set_RollBack` accessor. Measured live:

```
dir(UndoableUnitOfWorkHelper) rollback-ish -> ['RollBackChanges', 'set_RollBack']
hasattr(helper, "RollBack")               -> False
helper.RollBack = False                   -> "OK"   (silently accepted!)
```

So `helper.RollBack = False` never reached .NET. It landed as a plain Python
attribute on the wrapper while the real field kept its constructor default of
`True` (`UnitOfWorkHelper.cs:31`), and `Dispose()` therefore took the
`if (RollBack) RollBackChanges()` branch (`:115-116`) on **every** exit,
clean ones included.

This is the same silent-assignment failure mode already recorded in this
feature's concerns for `ILexEtymology.LanguageRA` — a pythonnet wrapper
accepting an attribute write that the underlying .NET type does not have.

### Control (proves the LCM itself was fine)

Driving the action handler directly, bypassing the helper:

```
ah.BeginUndoTask("TEST probe2", "TEST probe2")
p.POS.Create("TEST_probe_e", "TEST_pe")
ah.EndUndoTask()
-> count 5 -> 6, Find("TEST_probe_e") -> object, CanUndo() -> True
```

The write path was sound; only the commit/rollback flag was unreachable.

### Fix

`helper.set_RollBack(...)` at both call sites:

* `flexicon/code/transaction.py` — `_NestingAwareTransaction.__exit__`
* `flexicon/code/undoable_operation.py` — `_FLExUndoableOperation.__exit__`

### Post-fix live verification

| Case | Pre | Post |
|---|---|---|
| `_TransactionCM` clean exit (`POS.Create`) | 5 POS | 6 POS, `Find` → object, `CanUndo()` → `True` |
| `UndoableOperation` clean exit | 5 POS | 6 POS, `Find` → object |
| `UndoableOperation` raising block | 5 POS | 5 POS, `Find` → `None` (**still rolls back**) |

Both halves hold: clean exits commit, raising blocks roll back.

### Why 30 offline tests missed it

The doubles in `tests/test_b1t_action_handler_double.py` and
`tests/operations/test_transaction_rollback.py` modelled `RollBack` as an
assignable attribute, so the assignment "worked" offline. All previously
landed live verification ran on `target_sandbox`, which is `undoable=False`
— **Phase 2 had never been exercised against a live LCM at all.**

Both doubles now `raise AttributeError` on `helper.RollBack = ...` and expose
`set_RollBack(...)` instead, plus a source-level guard
(`test_source_never_assigns_the_rollback_property`) asserting neither module
contains a `.RollBack =` assignment and both call `set_RollBack(`.

---

## Part 3 — pre-existing defect found, RECORDED not fixed:
`SaveChanges()` is unusable under `undoable=False`

Surfaced when A3's first draft used `SaveChanges()` to establish committed
state. **Not caused by A3, and out of A3's scope.**

`undoable=False` holds the session envelope open, so the FSM sits in
`ProcessingDataChanges` for the whole session. `SaveChanges()` →
`UnitOfWorkService.Save()` → `SaveInternal()` →
`CheckReadyForCommit("Commit at wrong place.")`, which requires
`ReadyForBeginTask` (`UnitOfWorkService.cs:304`). Live result:

```
System.InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
```

So the **default** write mode cannot commit mid-session. Two aggravating
factors: per `UndoStack.cs:239-246` that check **rolls back the open bundle
before throwing**, so the failed save also discards the session's uncommitted
work; and it surfaces as a raw `System.InvalidOperationException` rather than
an `FP_*` error.

`CloseProject()` is unaffected — it calls `EndNonUndoableTask()` first,
returning the FSM to `ReadyForBeginTask` before `usm.Save()`.

Pinned by `TestSaveChangesIsUnusableInThisMode::
test_save_changes_raises_commit_at_wrong_place`, which asserts the **current
broken behaviour** so the defect is measurable. That test must be inverted
when the defect is fixed.

---

## Verdict

**PASS** — A3 verified live on Target.
Plus one critical pre-existing defect (B1 Phase 2 rollback) fixed and
verified live, and one pre-existing defect (`SaveChanges` under
`undoable=False`) recorded with a pinning test.
