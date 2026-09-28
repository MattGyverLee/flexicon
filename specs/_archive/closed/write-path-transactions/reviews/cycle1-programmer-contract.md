# Cycle 1 - Programmer - Contract baseline (task CB)

## What was added

- Fixed `extract_lcm_contract.py` auto-detect (stale post-rename: only
  looked for `flexlibs2/code`, never `flexicon/code`).
- New `tests/contract/pending_contract_seeds.py`: an AST-parseable, never-
  imported seed file that registers `IActionHandler`,
  `UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper` with the
  existing extractor (`ILcmUI` was already organic via `headless_ui.py`).
  Needed because B1 (transaction.py rewrite) hasn't landed, so no real
  source file imports these types yet - CB must land *before* B1 per
  tasks.md. `extract_contract()` now scans this file in addition to
  `flexicon/code` via a new `pending_seeds_path` param (default on).
- Extended `generate_lcm_snapshot._introspect_type` additively (new keys
  only, existing `properties`/`methods` derivation untouched, so none of
  the ~246 already-baselined types shift) with `constructors`,
  `method_signatures` (param-type lists, overload-aware),
  `interfaces`, `implements_idisposable`, and `reflected_properties`
  (catches write-only props like `RollBack` that the old dir()-based
  listing only surfaces as `set_RollBack`).
- New `TestTransactionLayerContract` class (6 tests) in
  `test_lcm_contract.py`, reading the checked-in `baseline_snapshot`
  fixture (Mode 1, no live liblcm needed to re-run).

## Regeneration

Regenerated (not hand-edited) via the existing CLIs:
`extract_lcm_contract.py -o snapshots/expected_contract.json`, then
`generate_lcm_snapshot.py -c expected_contract.json -o liblcm_baseline.json`
against live `SIL.LCModel.dll` (FieldWorks 9). Also picked up 3-4 files
added to `flexicon/code` since the last baseline regen (78-79 files vs the
stale 75), fixing two pre-existing false regressions (`IStTxtParaRepository`
removed, `ILcmUI` never added) as a side effect.

## Test results (real, `pytest tests/contract/ -q`)

22 passed, 0 failed. Before this change: 2 pre-existing failures
(`test_no_new_type_dependencies`, `test_no_regressions_from_baseline`) from
baseline drift unrelated to CB, now fixed by the regeneration.

## Confirmation vs #233/#235/#236

Verified by temporarily mutating a scratch copy of `liblcm_baseline.json` to
the pre-fix shapes and re-running: `test_action_handler_begin_undo_task_is_
two_string_args` fails on a 1-string-arg `BeginUndoTask` (#233), and
`test_action_handler_does_not_expose_rollback_to_mark` fails when
`RollbackToMark` is injected into the type (#236). #235 (`LcmCache.UndoStack`
non-existence) is covered structurally: `IActionHandler` is now baselined
with `Undo`/`Redo`/`CanUndo`/`CanRedo`, giving `test_action_handler_exposes_
expected_undo_redo_surface` a real target to check B3's `cache.
ActionHandlerAccessor` route against, rather than a member that was never
introspected at all. Reverted the scratch mutation before finishing; real
baseline was untouched by the check.
