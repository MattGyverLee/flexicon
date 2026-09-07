# Cycle 7 -- Programmer report: T8b, SaveChanges() depth guard

Landed the C21 guard in `flexicon/code/FLExProject.py::SaveChanges()`: reads
`self.CurrentDepth` (T1 surface) after the `writeEnabled` check, raises
`FP_TransactionError` with a mode-differentiated message when depth > 0
(before `usm.Save()` is ever attempted), fails OPEN (logs `WARNING`,
proceeds to `usm.Save()`) if the depth read itself raises. Corrected the
three shipped Examples (`SaveChanges()`, `RefreshFromDisk()`,
`AbortSession()`); `RefreshFromDisk()`'s note states only the depth
contract, not an unmeasured recovery claim.

**Measured P-5 survivor count: 25/25 -- matches the prediction, no flag
needed.** The guard leaves the envelope genuinely open (depth unchanged);
the "forced" manual End now succeeds for real, committing normally, and
`CloseProject()` persists an untouched change set. Phase-1 `else:` branch
WAS taken (`HasOpenSessionTask()` False, `EndNonUndoableTask()` skipped,
debug-confirmed) and the save succeeded -- recorded for T7's later C23
recut; `CloseProject()` not touched.

**P-10 flip (measured, not assumed):** Case A stays 25/25 both reads
(exception type now `FP_TransactionError`, depth stays at 1, no longer
collapses). Case C flips from T8a's frozen 0/25 to **25/25 both reads** --
the guard never lets the destructive raw `usm.Save()` run. Case B untouched.
Before/after table is in the evidence file; T8a's file is unedited as the
frozen "before".

**All 11 sites disposed:** (1) `test_abort_session_live.py`'s
`TestSaveChangesIsUnusableInThisMode` inverted to expect
`FP_TransactionError` + survives-in-memory, docstring rewritten
"defect"->"fixed"; (2) cross-reference prose updated; (3-5) P-5's
assertions/prose rewritten; (6-8) P-7/P-8/P-9 switched their trigger to the
raw `ObjectRepository(IUndoStackManager)` + `usm.Save()` accessor so they
keep exercising liblcm's no-op-commit mechanism unchanged by the guard --
pre-existing 0/25 and "Commit at wrong place." assertions still hold, all
passed live; (9) P-10 updated per above; (10)
`test_transaction_honesty.py`'s slice window widened -- **both**
`save_body` (1000->6000) **and** `refresh_body` (2500->4000, not named in
the brief but broken by the same cause, since `RefreshFromDisk()`'s
docstring also grew); (11) `manual_verification.py` line 526 updated
cheaply.

**P-11 (new, 10->11 live tests): a genuine P0 finding.** Predicted a priori
that letting `FP_TransactionError` escape `UndoableOperation()` would roll
back to 0/25, identical to today's uncaught-exception behavior. Measured:
**25/25 survived, both in-memory and on-disk**, despite the debug log
confirming `set_RollBack(True)` + `Dispose()` ran. Not a guard defect -- the
guard raised correctly -- this is a finding about what liblcm's own
`UndoableUnitOfWorkHelper.Dispose()`/`RollBack` actually does, independent
of the trigger (same exit path ran on any escaping exception pre-T8b). I
did not tune the assertion or dig into liblcm internals (out of scope); I
locked in the measured 25/25, documented the contradiction prominently in
the test docstring and evidence file, and flag it here for `/lex-lead` to
route. The shipped `undoable=True` docstring is NOT contradicted -- it only
describes the normal-exit commit path, silent on an escaping exception.

**Verification:** 11/11 probe-file and 12/12 abort-session live tests
green, `run_mode: live` confirmed twice, offline baseline 1290 passed
(deselected 474->475, exactly +1 for P-11). `git diff --stat` confirms only
`flexicon/code/FLExProject.py` and the enumerated test files were touched;
`CloseProject()`, `CHANGELOG.md`, `spec.md`, `tasks.md`, `QUEUE.md`
untouched (pre-existing changes from other crew members this cycle).

Files: `flexicon/code/FLExProject.py`,
`tests/operations/test_abort_session_live.py`,
`tests/operations/test_issue243_closeproject_probe.py`,
`tests/test_transaction_honesty.py`, `tests/manual_verification.py`,
`specs/243-closeproject-save-guard/evidence/live-t8b-savechanges-guard.md`.
