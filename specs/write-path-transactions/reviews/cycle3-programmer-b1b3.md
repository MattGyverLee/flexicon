# Programmer report — B1 + B3 (cycle 3)

**Scope executed:** B1 (`transaction.py` rewrite on `UndoableUnitOfWorkHelper`) and
B3 (`Undo()`/`Redo()` fix). No live FLEx project was opened; no live LCM write was
executed. All verification is offline/mocked, per the ABSOLUTE CONSTRAINT.

**Environment note:** FieldWorks 9 + SIL.LCModel are actually installed and
loadable on this machine (confirmed via the session-scoped `conftest.py`
fixture), so `SIL.LCModel.Infrastructure.UndoableUnitOfWorkHelper` etc. resolve
to the real .NET types at import time. I never opened a project or touched a
live `LcmCache` — all Phase 2 tests substitute a plain-Python fake for
`UndoableUnitOfWorkHelper` and a plain-Python fake `IActionHandler`, so nothing
in this cycle exercised real LCM state.

## B1 — `transaction.py` rewrite

### What changed, per file

**`flexicon/code/transaction.py`** (rewritten)
- `_NestingAwareTransaction.__enter__`/`__exit__` completely rewritten.
  - Phase 1 (`_undoable=False`): unchanged behavior — always delegates to
    `project.Transaction(label)`, regardless of depth (Phase 1 never opens an
    LCM undo task at all; the session-long non-undoable envelope is opened
    once at `OpenProject()`).
  - Phase 2 (`_undoable=True`): reads `project.project.ActionHandlerAccessor.CurrentDepth`
    at every `__enter__`. If `> 0`, joins (no-op, runs the body only). If `0`,
    constructs `SIL.LCModel.Infrastructure.UndoableUnitOfWorkHelper(action_handler,
    label, label)` directly (module-level import, not lazy — see "testability"
    below). On `__exit__`, sets `helper.RollBack = exc_type is not None` then
    calls `helper.Dispose()` — this is a write-only property (no getter), so it
    is only ever set, never read back.
  - `_transaction_depth` deleted outright: no attribute is set, read, or
    referenced anywhere in this file (grep-clean, see audit below).
  - `_FLExTransaction` (Phase 1 mark/rollback wrapper) is untouched — same class,
    same `(None, None)` behavior, same docstrings (this class is A2/#236 scope,
    not B1).

**`flexicon/code/undoable_operation.py`** (rewritten) — *scope note below*
- `_FLExUndoableOperation.__init__` signature changed from
  `(project, label, begin_undo_fn, end_undo_fn)` to `(project, label)`.
- `__enter__` no longer calls a discovered `begin_undo_fn(label)` with one
  argument against liblcm's two-argument `IActionHandler.BeginUndoTask(String,
  String)` — that one-argument call was the literal #233 bug. It now reads
  `CurrentDepth` and either joins or constructs `UndoableUnitOfWorkHelper(action_handler,
  label, label)` directly — same join/open idiom as `_NestingAwareTransaction`.
- `__exit__` sets `RollBack` and calls `Dispose()`, same as `_NestingAwareTransaction`.

**Why `undoable_operation.py` was also touched.** The task text scoped B1 as
"rewrite `flexicon/code/transaction.py`", with "fix the `BeginUndoTask` arity
bug (#233)" as one of four required changes. Per `spec.md`'s own reachability
table, #233 previously fired "only in the `elif undoable:` branch at
`transaction.py:64-65`" — i.e. via `_NestingAwareTransaction` calling
`project.UndoableOperation(label)`. Once `_NestingAwareTransaction` was rewritten
to construct `UndoableUnitOfWorkHelper` directly (bypassing `UndoableOperation()`
entirely), that reachable path was closed. But `FLExProject.UndoableOperation()`
is also public API, documented and callable directly, and the same one-argument
`BeginUndoTask` bug still lived there (`_GetUndoRedoAPI` + `_FLExUndoableOperation`).
Leaving it would mean #233 was patched around, not fixed — a second, still-buggy
door to the same failure mode. I rewrote it using the identical idiom rather than
inventing a second design, and deleted `FLExProject._GetUndoRedoAPI()` entirely
(no callers left, no test locked its behavior — confirmed by grep before deleting).
If this scope expansion is judged too broad for this cycle, `undoable_operation.py`
and the `UndoableOperation()`/`_GetUndoRedoAPI` edit in `FLExProject.py` are the
files to revert; `_NestingAwareTransaction` alone still satisfies the letter of
the 174-site compatibility requirement either way.

**`flexicon/code/FLExProject.py`**
- `OpenProject()`: deleted `self._transaction_depth = 0` and its docstring
  comment; replaced with a note explaining the deletion and pointing at
  `ActionHandlerAccessor.CurrentDepth`.
- `Transaction()` docstring: corrected the stale "once B1 lands, `Transaction()`
  becomes genuinely transactional" claim. **`Transaction()` itself is
  unchanged and intentionally NOT rewired to `_NestingAwareTransaction`** — this
  is locked by an existing, un-editable regression test
  (`tests/test_transaction_honesty.py::TestTransactionHonesty::test_transaction_body_always_passes_none_none`,
  which asserts the method body always constructs
  `_FLExTransaction(self, label, None, None)`). Only the internal
  `BaseOperations._TransactionCM()` wrapper (i.e. all 174 sites) got the real
  rollback; a direct `project.Transaction(label)` call remains Phase-1-only in
  both modes.
- `UndoableOperation()`: docstring Note rewritten to describe the new
  rollback-capable behavior; body simplified to
  `return _FLExUndoableOperation(self, label)`.
- `_GetUndoRedoAPI()`: deleted in full.
- `Undo()`/`Redo()` (B3, below).

**`flexicon/code/BaseOperations.py`**
- `_TransactionCM()` docstring `Notes:` section rewritten: the old claim
  "Phase 2 ... does NOT auto-rollback on exception either" is now false and was
  corrected to state Phase 2 IS rollback-capable; the nesting-guard description
  was rewritten from "`project._transaction_depth`" to
  "`cache.ActionHandlerAccessor.CurrentDepth`, asked fresh at every `__enter__`".
  (`test_baseoperations_transactioncm_docstring_no_longer_claims_rollback` in
  `test_transaction_honesty.py` still passes — it only requires the Phase 1
  "does NOT roll back" sentence to survive, which it does.)

**`docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`**
- Two passages describing `_NestingAwareTransaction` as "reads
  `project._transaction_depth`" were updated to describe the landed
  `cache.ActionHandlerAccessor.CurrentDepth`-based implementation (these two
  spots asserted present-tense behavior, not historical narrative, so they would
  have gone stale the moment B1 landed). Left the forward-looking migration-path
  line ("Land B1 ... deletes `_transaction_depth`") untouched — it correctly
  describes what B1 does, tense-neutral.

### The exact join-vs-open logic used

Verbatim shape from `UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW`
(`UndoableUnitOfWorkHelper.cs:94-97`), translated into the constructor/Dispose
shape a Python context manager needs (no callable body to hand `Do()`):

```python
depth = project.project.ActionHandlerAccessor.CurrentDepth
if depth > 0:
    ... join: do nothing, just let the body run ...
else:
    helper = UndoableUnitOfWorkHelper(action_handler, label, label)  # opens
    ... run body ...
    helper.RollBack = exc_type is not None   # False -> commit, True -> rollback
    helper.Dispose()
```

No variant was invented — the only departure from the literal C# idiom is
unavoidable: a Python `with` block can't hand liblcm a `System.Action` the way
`Do()` wants one, so "open" is expressed as construct-now / dispose-at-`__exit__`
rather than a single `Do(...)` call. The two facts from cycle 2's review were
applied directly: `RollBack` defaults to `True` from the constructor
(`UnitOfWorkHelper.cs:31`) and is write-only (no getter, confirmed in
`liblcm_baseline.json`'s `reflected_properties.RollBack: {can_read: false,
can_write: true}`), so the code only ever *sets* it, never reads it back.

### Clearing the RollBack flag on the success path

`self._helper.RollBack = exc_type is not None` runs unconditionally in
`__exit__` before `Dispose()` — on a clean exit `exc_type` is `None`, so
`RollBack` becomes `False` (commit/`EndUndoTask()`); on an exception it stays
effectively `True` (rollback/`Rollback(0)`, matching the ctor default). This
matches `spec.md`'s own B1 pseudocode exactly (`self._helper.RollBack = exc_type
is not None`).

### `_transaction_depth` removal audit

`grep -rn "_transaction_depth" .` (excluding `.git`) after all edits, in full:

- **Code (must be zero, and is):** `flexicon/code/*.py` — zero hits.
- **Test code (fixed, not just grep-silenced):**
  - `tests/operations/test_inflection_features.py:649` — dead mock-setup line
    removed (Phase 1 project, never consulted `_transaction_depth` even before
    B1; removing it changes nothing observable).
  - `tests/operations/test_segment_operations.py:743` — same, removed.
  - `tests/operations/test_transaction_rollback.py` — full rewrite (see Test
    Results below); `_transaction_depth` assertions replaced with
    `CurrentDepth`-based assertions against a fake `IActionHandler`.
- **Prose (left as historical/explanatory, not an executable read):**
  `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:488` (names what B1's commit message will
  say), `flexicon/code/FLExProject.py` comment, `flexicon/code/transaction.py`
  docstring (worded to avoid the literal `project._transaction_depth` substring
  so a source-scan regression test — see below — can assert its absence
  unambiguously), and the pre-existing `spec.md`/`tasks.md`/`reviews/cycle2-*`
  planning artifacts, which I did not touch (lead-owned, describe history).

A dedicated regression test
(`TestPhase2JoinOrOpen::test_no_local_transaction_depth_attribute_referenced_in_source`
in `test_transaction_rollback.py`) asserts `"project._transaction_depth" not in
source` and `"self._transaction_depth" not in source` against
`flexicon/code/transaction.py`'s actual file contents, so this isn't just a
point-in-time grep — it's enforced going forward.

### 174-site compatibility check

```
grep -rn "with self._TransactionCM(" flexicon/code --include=*.py | wc -l
174
```
Confirmed both before and after all edits (the earlier apparent "176" was two
`__pycache__/*.pyc` binary-grep matches, not source hits — filtering to `*.py`
gives 174 cleanly). Zero of the 174 call sites were edited.

### Liblcm members used vs. the baseline

Every member touched is present in `tests/contract/snapshots/liblcm_baseline.json`:
- `UndoableUnitOfWorkHelper` ctor `(IActionHandler, String, String)` — present
  (`method_signatures` / `constructors`).
- `UndoableUnitOfWorkHelper.RollBack` — present, `can_write: true, can_read:
  false` (confirms the write-only handling above is correct, not a guess).
- `UndoableUnitOfWorkHelper.Dispose()` — present.
- `IActionHandler.CurrentDepth`, `.CanUndo()`, `.CanRedo()`, `.Undo()`,
  `.Redo()`, `.BeginUndoTask(String, String)` — all present.
- `LcmCache.ActionHandlerAccessor` — present (`get_ActionHandlerAccessor`,
  type `IActionHandler`).

**No member I needed was absent from the baseline.** I did not invoke
`generate_lcm_snapshot.py` against a live cache this cycle (out of scope /
would need a live project); all checks above were against the already-extended
baseline JSON, per the ABSOLUTE CONSTRAINT.

## B3 — `Undo()`/`Redo()`

Both rewritten to read `self.project.ActionHandlerAccessor` (the `LcmCache`
property, confirmed present in the baseline) instead of the non-existent
`self.project.UndoStack`. Both gate on `CanUndo()`/`CanRedo()` before calling
`Undo()`/`Redo()`, since (per cycle-2 facts) an empty-stack `Undo()`/`Redo()`
throws rather than returning a status. The old `if undo_stack is None:` /
`else:` dead branches (both were unreachable once `UndoStack` was correctly
identified as never existing) are deleted; both methods are now: guard on
`_undoable` → guard on `Can{Undo,Redo}()` → call → wrap unexpected exceptions in
`FP_TransactionError`. Both docstrings state the in-process-only scope
verbatim, per the task's requirement, including the concrete facts backing it
(`Stack<UnitOfWork>` in RAM, live `ICmObject` refs, no `.fwdata` serializer,
fresh `LcmCache` starts at `UndoableActionCount == 0`) and a pointer to where
cross-*session* reversal is tracked instead (`flexicon/sync/engine.py`'s
`create_snapshot`/`Snapshot` stubs), so the scope statement can't be misread as
"this is impossible to ever fix anywhere."

## Test results

**Before** (baseline, captured via `git stash` back to the pre-cycle commit,
`pytest -m "not requires_live_project" -q`):
`117 failed, 1373 passed, 11 skipped, 322 deselected, 17 errors, 5 subtests passed`

**After** (all edits applied, stash popped):
`117 failed, 1394 passed, 11 skipped, 322 deselected, 17 errors, 5 subtests passed`

The two `FAILED` line lists (sorted) are **byte-identical** between before and
after (`diff` exit code 0) — the 117 pre-existing failures are unrelated to
this change (mostly `flexicon/sync/tests/*`, `test_consolidation_coverage.py`,
`test_itsstring_fix.py`, etc.) and none of them were caused or fixed by this
work. The +21 passed are new tests I added:

- `tests/operations/test_transaction_rollback.py`: rewritten, 13 → 20 tests
  (+7). Covers Phase 1 unchanged behavior, Phase 2 join-vs-open, RollBack
  True/False on exception/clean-exit, the `#233` ctor-arity regression lock
  (asserts the helper is always constructed with both undo and redo text), and
  `_FLExUndoableOperation` (the `UndoableOperation()` public entry point)
  directly.
- `tests/test_undo_redo.py`: new file, 14 tests. Covers B3's `Undo()`/`Redo()`
  guard/gate/wrap logic and the in-process docstring scope caveat.
- `test_undo_redo_mocked.py` (pre-existing, root-level legacy script, tracked
  in git since v2.4.0): 2 of its 7 tests called the OLD 4-argument
  `_FLExUndoableOperation(project, label, begin_fn, end_fn)` constructor and
  would have failed with a `TypeError` under the new 2-argument signature. Fixed
  both call sites to the new 2-argument form; all 7 still pass (verified both
  via `pytest` and via its own `if __name__ == "__main__"` runner).
- `tests/operations/test_inflection_features.py`,
  `tests/operations/test_segment_operations.py`: one dead
  `project._transaction_depth = 0` mock-setup line removed from each (Phase 1
  fixtures; the line was never consulted even before this change).

Full contract suite (`pytest tests/contract/ -q`): 22 passed, 0 failed.
`tests/test_transaction_honesty.py` (Track A regression suite, including the
test that locks `Transaction()`'s exact body): 12 passed, 0 failed.

## Things I deliberately did NOT do

- Did not touch `spec.md`, `tasks.md`, or `reviews/cycle2-*` (lead-owned
  planning artifacts; historical narrative mentioning the old
  `_transaction_depth` name is accurate as history and left alone).
- Did not touch `tests/contract/pending_contract_seeds.py`. Its own doc comment
  says the `IActionHandler`/`UndoableUnitOfWorkHelper` seed section can be
  deleted "once transaction.py (B1) imports and uses them for real." The
  *import* is now organic, but the AST extractor
  (`LCMContractVisitor.visit_Attribute`/`visit_Call`) only tracks the literal
  `TypeName.member` form on the imported name itself — my code always goes
  through an instance variable (`action_handler.CurrentDepth`,
  `self._helper.Dispose()`), which the extractor's own file-level comment
  already documents as untrackable ("not literally how instance calls read in
  real code"). So the seed's member-level entries (`CurrentDepth`,
  `BeginUndoTask`, `CanUndo`, etc., and `UndoableUnitOfWorkHelper.Dispose()`)
  remain necessary; only the bare `from ... import UndoableUnitOfWorkHelper`
  became organic. Deleting the seed file's member section would have silently
  dropped contract coverage. Confirmed by running `tests/contract/` after —
  still 22/22 green with the seed file untouched.
- Did not attempt B2 (bracketing the 294 single-mutation setters) or B2t (the
  live-project persistence test) — both explicitly out of scope / gated
  `needs_human`.
- Did not commit. Left `specs/write-path-transactions/reviews/cycle3-programmer-b2g.md`
  and `tests/write_path_transactions/` untouched (untracked files present at
  session start, not mine, appear to belong to a parallel B2g effort).

## Files touched

- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\transaction.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\undoable_operation.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\FLExProject.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\BaseOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\docs\FLEXTOOLSMCP_WRITE_CONTRACT.md`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_transaction_rollback.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\test_undo_redo.py` (new)
- `D:\Github\_Projects\_LEX\flexicon\test_undo_redo_mocked.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_inflection_features.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_segment_operations.py`
