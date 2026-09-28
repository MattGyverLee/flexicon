# Cycle 2 P0 Fix — FP_ConflictingSaveError Hierarchy + P1/P2 wording

## P0 (blocking) — done

- **Moved** `FP_ConflictingSaveError` from `flexicon/code/headless_ui.py:66`
  into `flexicon/code/exceptions.py` (new class, end of file, after
  `FP_TransactionError`).
- **Subclassed `FP_RuntimeError`**, not `FP_ProjectError`: the condition is
  discovered mid-session on a save that happens after the project is already
  open (a runtime failure of an in-progress write), matching the existing
  split between "problems opening the project" (`FP_ProjectError`) and
  "problems running the module" (`FP_RuntimeError`) in `exceptions.py:12/53`.
- **`headless_ui.py`**: removed the local class def; now does
  `from .exceptions import FP_ConflictingSaveError` (line ~62) so
  `from flexicon.code.headless_ui import FP_ConflictingSaveError` still
  resolves (back-compat, verified by identity check).
- **Exported** from `flexicon/code/FLExProject.py`'s `.exceptions` import
  block and from `flexicon/__init__.py`'s `.code.FLExProject` import block,
  alongside the other `FP_*` types. `flexlibs2` alias package picks it up
  automatically (verified: `flexlibs2.FP_ConflictingSaveError is
  flexicon.FP_ConflictingSaveError`).
- **`docs/EXCEPTION_HANDLING.md`**: added to the Runtime Exceptions hierarchy
  list and to the "Import flexlibs2 Exceptions" code block (was lines
  622-635).
- **`tests/test_headless_lcm_ui.py`**: `_import_headless_ui()` now imports
  `FP_ConflictingSaveError`/`FP_RuntimeError` from the canonical
  `flexicon.code.exceptions`, returns `FP_RuntimeError` too (fixed 3 call
  sites that unpacked a fixed-length tuple), and a new test
  `test_conflicting_save_error_is_an_fp_runtime_error` asserts
  `issubclass(FP_ConflictingSaveError, FP_RuntimeError)`.

## P1/P2 (non-blocking) — done

- **Q2 wording**: reworded "one-shot" -> "per-session" in the two docstrings
  that actually contained the ambiguous phrase: `FLExProject.py` (Transaction
  docstring, ~line 472) and `transaction.py` (`_FLExTransaction.__enter__`
  docstring, ~line 150). Added an explicit "not once per process or per
  instance -- a second `OpenProject()` call in the same session re-logs it"
  clause. **Note:** `BaseOperations.py` does not contain "one-shot" wording
  anywhere (verified by grep of `one-shot`, `once`, `logged once`,
  `OpenProject`) — the `_TransactionCM` docstring discusses the same
  no-rollback limitation but never uses the ambiguous term, so nothing
  needed changing there. No behavior changed anywhere.
- **Q3**: added a comment block above
  `test_no_rollbacktomark_string_anywhere_in_flexicon_code`
  (`tests/test_headless_lcm_ui.py`) noting the sweep is blind to the same
  capability resurfacing under a renamed API.
- **P2 header**: `transaction.py:1-11` header now lists both
  `_NestingAwareTransaction` and `_FLExTransaction`.

## Untouched per instructions
`_TransactionCM` behavior/signature, and the `RefreshFromDisk` writeEnabled
guard/docstring — left exactly as-is (contested, escalated separately).

## Verification (actual, not rounded)

- `pytest tests/test_headless_lcm_ui.py -v`: **22 passed** (was 21 + 1 new
  hierarchy-regression test), 0 failed/skipped.
- `pytest tests/test_transaction_honesty.py -v`: **12 passed**, 0
  failed/skipped (confirms the "one-shot" reword didn't break the
  string-sweep test at `TestOneShotWarningAtOpenProject`).
- Full suite, run from repo root exactly as `pytest --ignore=tests/contract -q`
  (this collects 1813 items; `pytest tests/ --ignore=tests/contract` only
  collects 1481 and undercounts vs. baseline — noting this since a prior
  miscount was flagged): **139 failed, 1638 passed, 20 skipped, 17 errors**.
  Baseline was 1637 passed / 139 failed / 20 skipped / 17 errors — failed,
  skipped, and errors are identical; passed is +1, which is exactly the one
  new hierarchy test added above. No other numbers moved.

**Files changed:** `flexicon/code/exceptions.py`, `flexicon/code/headless_ui.py`,
`flexicon/code/FLExProject.py`, `flexicon/__init__.py`,
`flexicon/code/transaction.py`, `docs/EXCEPTION_HANDLING.md`,
`tests/test_headless_lcm_ui.py`.
