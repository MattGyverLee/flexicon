# Evidence -- P-11 re-measurement (issue #579)

Date: 2026-09-28
Fixture: `target_sandbox_path` ONLY (tempdir copies of the Target `.fwbackup`).
The real Target project was never opened; no `scripts/restore_*.py` was run.

## Question

T8b's P-11 measured 25/25 LexEntry creations surviving an
`FP_TransactionError` escaping a `with project.UndoableOperation(...)`
block, contradicting the rollback promise. A second measurement
(`transaction.py:146-153`, a created POS vanishing on clean exit) got the
opposite result. Which is true?

## Finding: P-11 measured the wrong set

P-11 creates its 25 entries BEFORE the `with` block
(`test_issue243_closeproject_probe.py:1926` creates, `:1933` enters the
block; the block body contains only `project.SaveChanges()`). Each bare
`Create` outside a block opens and commits its own per-operation
UnitOfWork, so 25/25 survival is the CORRECT outcome -- there was nothing
inside the block's UnitOfWork to roll back. The POS counter-measurement
(creations inside a block, discarded) is consistent with rollback working,
not opposite to P-11.

## Re-measurement (throwaway probe, `tests/operations/test_p11_remeasure_tmp.py`, since removed; content preserved below)

Two tests, both on `target_sandbox_path` with genuine close-and-reopen
re-reads:

- `test_p11r_creates_inside_block_with_escaping_fp_error`: 10 LexEntry
  creates INSIDE the block, then `project.SaveChanges()` raises
  `FP_TransactionError` at depth 1 and escapes.
- `test_p11r_creates_outside_block_control`: P-11 exact shape -- 10
  creates BEFORE the block, `SaveChanges()` raising inside.

### Commands

```
$ python -m pytest tests/operations/test_undoable_mode_live.py::TestExceptionRollsBackLive -m requires_live_project --collect-only -q
5 tests collected
$ $env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_undoable_mode_live.py::TestExceptionRollsBackLive -m requires_live_project -q
5 passed
$ $env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest "tests/operations/test_issue243_closeproject_probe.py::test_p11_case_a_exception_propagates_and_rolls_back" -m requires_live_project -q
1 passed
$ $env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_p11_remeasure_tmp.py -m requires_live_project -q -s
2 passed
```

### Results

| Case | In-memory (still-open re-read) | On-disk (close-and-reopen) |
|---|---|---|
| Creates INSIDE + escaping FP_TransactionError | 0/10 | 0/10 |
| Creates OUTSIDE (P-11 shape, control) | 10/10 | 10/10 |
| `TestExceptionRollsBackLive` (inside + generic `_Boom`, pre-existing) | gone (5/5 green) | durable (covered by `test_a_rolled_back_write_does_not_persist`) |

`tests/live_status.json` after these runs: `"run_mode": "live"`.

Console lines (verbatim):

```
[P11R-IN] in-memory after rollback exit: 0/10
[P11R-IN] on-disk after reopen: 0/10
[P11R-IN] VERDICT: 0/10 both reads -- rollback WORKS (docs bug, not code bug)
[P11R-OUT] in-memory: 10/10
[P11R-OUT] on-disk: 10/10
[P11R-OUT] VERDICT: 10/10 both reads -- control confirms P-11 measured the outside set
```

## PASS/FAIL line

**PASS.** Rollback discards the block's own mutations for the exact
exception type P-11 used. No code change: the defect is the
`undoable_operation.py::__exit__` docstring caveat (2026-09-07, C25),
corrected in the same change as this file (issue #579, filed P1
docs-only). `docs/EXCEPTION_HANDLING.md`'s "Atomicity Under
`undoable=True`" guarantee stands verified. Phase 1 `Transaction()`
(undoable=False) still has no rollback (mark_fn None, issue #236) --
that half of `docs/TRANSACTION_GUIDE.md` is unaffected.

## Thrown-away probe source (for the record; the file itself was removed after the run)

```python
# test_p11_remeasure_tmp.py -- THROWAWAY P-11 re-measurement (do not commit).
import pathlib
import pytest
pytestmark = pytest.mark.requires_live_project
TEST_PREFIX = "TEST_"
N = 10

def _count(project, prefix):
    n = 0
    for e in project.LexEntry.GetAll():
        form = project.LexEntry.GetLexemeForm(e)
        if form and form.startswith(prefix):
            n += 1
    return n

# test_p11r_creates_inside_block_with_escaping_fp_error:
#   open undoable=True on target_sandbox_path;
#   with UndoableOperation: create 10 prefixed entries, assert 10 visible,
#   then SaveChanges() (raises FP_TransactionError at depth 1, escapes);
#   re-read still-open count (expect 0), CloseProject, reopen read-only,
#   re-read count (expect 0).
# test_p11r_creates_outside_block_control:
#   open undoable=True; create 10 BEFORE the block;
#   with UndoableOperation: SaveChanges() only (raises, escapes);
#   re-read still-open (expect 10), CloseProject, reopen, re-read (expect 10).
```
