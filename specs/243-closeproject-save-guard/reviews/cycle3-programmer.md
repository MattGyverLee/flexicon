# Cycle 3 -- Programmer report: T2 (CP-A2), issue #243

## Finding: delegation is NOT behaviour-preserving at any of the three sites

All three sites were tried and empirically confirmed to break the offline
suite when pointed at `FLExProject._ReadActionHandlerDepth()`, wrapped in
each site's own lenient `try/except`:

- **`transaction.py:172`** (`_current_depth`): `project._ReadActionHandlerDepth()`
  -> **9 failed** in `test_b1t_action_handler_double.py` +
  `test_transaction_rollback.py` (was all-green).
- **`undoable_operation.py:102`**: `self._project._ReadActionHandlerDepth()`
  -> **2 failed**, same two files.
- **`System/CustomFieldOperations.py:306`**: `self.project._ReadActionHandlerDepth()`
  -> **2 failed** in `test_custom_field_create_refusal.py`.

**Root cause, all three:** every offline test exercising these sites hands
a bare `Mock()`/`MagicMock()` (no `spec=`) as the project object. Such
mocks auto-vivify any attribute -- including `._ReadActionHandlerDepth` --
into a child mock that, when called, returns another mock rather than
raising `AttributeError`. No `except` clause can catch a call that
"succeeds" with a wrong-typed value. An `isinstance(depth, int)` fallback
(mirroring `transaction.py`'s own pattern) makes it type-safe but silently
substitutes `0` for a depth of `1` the test explicitly configured via
`.ActionHandlerAccessor.CurrentDepth = ...` -- a join-vs-open /
guard-fires-vs-not LOGIC change, not exception-safety nuance.
`CustomFieldOperations.py` also fails a static source-grep test requiring
the literal strings `"ActionHandlerAccessor"`/`"CurrentDepth"` to stay in
the file.

Per the brief's own instruction, each site was **left unchanged** rather
than forced. `git diff --stat flexicon/code/` = empty; all three tentative
patches were fully reverted before the final run. The natural except
clause, had it worked, would have been `(FP_ProjectError, AttributeError)`
-- moot here since the actual doubles never raise `AttributeError`.

## No behaviour changed

`transaction.py`, `undoable_operation.py`, `CustomFieldOperations.py` are
byte-identical to T1's HEAD (`f3a0f50`).

## BEFORE/AFTER (offline)

BEFORE (HEAD, unedited): `1290 passed, 470 deselected`.
AFTER (0 diff): `1290 passed, 470 deselected`. Unchanged, as expected.

## Live suites

`tests/live_status.json` `"run_mode": "live"`.
- `test_transaction_rollback.py` -- **0 tests collected** under
  `-m requires_live_project` (carries no such marker; a fully offline file
  despite its name; flagged, not substituted).
- `test_custom_field_multistring_best_alt.py` -- `1 skipped`
  (pre-existing env-dependent skip, needs a live project with a
  pre-configured MultiString custom field; unrelated to T2).
- `test_undoable_mode_live.py` -- `33 passed`.

Full detail: `evidence/live-t2-internal-callsite-dedup.md`.

## Recommendation

Leave all three sites as-is; C5 already made this consolidation optional.
CP-A2 should close on this finding rather than a diff. Recommend
`/lex-lead` review before CP-B.

## PASS/FAIL

FAIL to implement as specified; PASS as verification (zero regression
because zero code changed).
