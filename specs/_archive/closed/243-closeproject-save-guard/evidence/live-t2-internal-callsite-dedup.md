# Evidence -- T2 internal call-site dedup (issue #243, CP-A2)

## Outcome

T2 could NOT be landed as a code change. Delegating any of the three
lenient call sites to `FLExProject._ReadActionHandlerDepth()` breaks the
existing offline suite. All three sites are LEFT UNCHANGED (0 diff in
`flexicon/code/`). See `reviews/cycle3-programmer.md` for the full finding.

## Commands, exactly as specified

### Offline suite -- BEFORE (HEAD = f3a0f50, unedited)

```
python -m pytest tests -m "not requires_live_project" -q
```
Result: `1290 passed, 470 deselected, 17 warnings in 12.85s`

### Offline suite -- AFTER (post-investigation, 0 diff in flexicon/code/)

```
python -m pytest tests -m "not requires_live_project" -q
```
Result: `1290 passed, 470 deselected, 17 warnings in 13.88s`

**BEFORE == AFTER: 1290 passed, both runs.** No regression, because no
functional code changed (git diff --stat flexicon/code/ = empty).

### Diagnostic runs (not part of the final suite -- these are the evidence
that delegation is NOT behaviour-preserving; each patch below was applied,
tested, then reverted in full before moving to the next site)

1. `transaction.py:172` (`_current_depth`) patched to
   `depth = project._ReadActionHandlerDepth()` (wrapped in
   `try/except Exception: depth = 0`):
   ```
   python -m pytest tests/test_b1t_action_handler_double.py tests/operations/test_transaction_rollback.py -m "not requires_live_project" -q
   ```
   Result: **9 failed, 43 passed** (was all-passing before the patch).
   Failures: `TestNestingJoins` (2), `TestNoDepthLeak` (3),
   `TestRollbackInvocation` (1), `TestPhase2JoinOrOpen` (3) -- all because
   `project` in these tests is a bare `Mock()`, so
   `project._ReadActionHandlerDepth()` auto-vivifies as a callable Mock
   returning a non-int Mock instead of raising, and the nesting/join logic
   silently reads depth as 0 (via the isinstance fallback) when the real
   answer (from `project.project.ActionHandlerAccessor.CurrentDepth`,
   explicitly set on the double) is 1. Reverted.

2. `undoable_operation.py:102` patched to
   `depth = self._project._ReadActionHandlerDepth()` (same wrapper):
   ```
   python -m pytest tests/test_b1t_action_handler_double.py tests/operations/test_transaction_rollback.py -m "not requires_live_project" -q
   ```
   Result: **2 failed, 50 passed**. Same root cause (`self._project` is a
   bare `Mock()` in `_phase2_project()` / `_make_project()`). Reverted.

3. `System/CustomFieldOperations.py:306` patched to
   `depth = self.project._ReadActionHandlerDepth()` (same wrapper):
   ```
   python -m pytest tests/test_custom_field_create_refusal.py -m "not requires_live_project" -q
   ```
   Result: **2 failed, 5 passed**. `project = MagicMock()` in
   `test_guard_raises_at_runtime` auto-vivifies `_ReadActionHandlerDepth`
   (a MagicMock call returns another MagicMock, no exception), so `depth`
   falls back to 0 via the isinstance guard and the depth>0 branch never
   fires -- `CreateField` reaches the wrong `FP_TransactionError` (the
   "not yet implemented" one, missing "AddCustomField" in its message),
   failing the test's message-content assertion. A SECOND, independent
   failure also fires: `test_checks_action_handler_current_depth` is a
   static source-text grep for the literal substrings `"ActionHandlerAccessor"`
   and `"CurrentDepth"` in `CustomFieldOperations.py`; delegating removes
   both literals from the source. Reverted.

All three patches were reverted before the final `git diff --stat
flexicon/code/` check (empty) and before the final offline run recorded
above.

### Live suites

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_transaction_rollback.py -m requires_live_project -q
python -m pytest tests/operations/test_custom_field_multistring_best_alt.py -m requires_live_project -q
python -m pytest tests/operations/test_undoable_mode_live.py -m requires_live_project -q
```

(Run via the Bash tool's `export FLEXLIBS_REQUIRE_LIVE=1 &&` equivalent;
same effect.)

| File | Result | Note |
|---|---|---|
| `tests/operations/test_transaction_rollback.py` | **`20 deselected` -- 0 tests collected under `-m requires_live_project`** | This file carries NO `requires_live_project` marker anywhere (grep confirmed) -- it is a fully offline Mock/patch-based unit-test file despite its name. Flagging per the task's instruction not to report a zero-test run as a pass: this is NOT a live pass, it is zero tests. Its offline coverage of these three sites IS exercised (see diagnostic run #1 above via `-m "not requires_live_project"`). |
| `tests/operations/test_custom_field_multistring_best_alt.py` | `1 skipped` | Same result before and after (0 code diff). Skip is pre-existing and environment-dependent: the test needs one of `Sena 3` / `Test` / `SampleLexicon` / `SampleLexicon3` already open with a MultiString custom field configured via the FLEx UI; none was found in this environment. Unrelated to T2 (this file is untouched by any of the three call sites). |
| `tests/operations/test_undoable_mode_live.py` | `33 passed` | `tests/live_status.json` `"run_mode": "live"` (confirmed by direct read after this run, `run_timestamp: 2026-09-07T09:28:57Z`). Same result before and after (0 code diff). |

`run_mode` read from `tests/live_status.json`: **`"live"`** (not mock).

## PASS/FAIL

**PASS -- as a verification exercise, FAIL as a code change.** No
regression was introduced (offline 1290/1290 unchanged, live suites
unchanged) because no code was changed. T2's originally-specified shape
(delegate all three sites to the shared helper) is NOT achievable without
breaking the offline suite; see `reviews/cycle3-programmer.md` for the
finding and recommendation.
