# Cycle 8 -- Programmer report: T7 (C23 recut)

Implemented T7 exactly as recut by `spec.md` C23. `CloseProject()`'s Phase-1
`else:` branch now logs at ERROR (not debug), naming the anomaly
(`HasOpenSessionTask()` read `False` inside Phase 1, unreachable by
construction unless the envelope was already ended early) and stating
plainly that `usm.Save()` proceeds anyway -- asserting nothing about data
loss. The withdrawn `FP_ProjectError` raise was NOT reintroduced. C18's
detector is unchanged in logic: the branch entry is the primary signal; a
pre-`Save()` `HasUnsavedChanges` read is logged as a raw diagnostic value
only, wrapped in its own `try/except`, gating nothing, and never worded as
"nothing pending to save". C15's `Dispose()`/`del self.project` moved into
a `finally` wrapping the write/save block. `undoable_operation.py` gained
the dated C25 caveat (T8b's P-11 measurement, object-creation only, zero
executable-line change).

Checked `transaction.py` per the brief: found a surviving rollback-discards
claim (lines ~146-153, "a created POS vanished on clean exit" under the
`.RollBack = False` assignment-bug scenario). This is a different measured
scenario from P-11 (an assignment bug, not an escaping exception), so not
directly contradictory, but flagging per instruction. Not edited.

Extended the existing P-4/P-5 live tests with `caplog` assertions rather
than adding a new live test (live count held at 11). Added exactly one new
OFFLINE/MOCK test for C15's `finally` guarantee (`usm.Save()` raising is
not reachable on any live route measured so far). To let that offline test
coexist without inheriting the file's blanket live marker, replaced the
module-level `pytestmark` with an individual `@pytest.mark.requires_live_project`
decorator on each of the 11 pre-existing tests -- mechanical, zero
behaviour change, confirmed by an unchanged 11/11 live pass and unchanged
475 offline deselection count.

One self-correction worth flagging: my first cut of the ERROR message
included the phrase "asserts nothing about whether data was lost", which
of course contains the substring "lost" and tripped my own no-loss-claim
assertion. Reworded the message to drop the word entirely rather than
loosen the test -- the message now states facts only (branch taken,
`usm.Save()` proceeding, diagnostic value) with no loss-related vocabulary
at all. No other prediction was contradicted this cycle: P-4 fired zero
ERROR records (control), P-5 fired exactly one, both survived 25/25.

**Live:** probe file 11/11 passed (1 offline test deselected, correctly);
`test_abort_session_live.py` 12/12 passed, unaffected; `run_mode: live`
confirmed at `2026-09-07T17:01:58Z`. **Offline:** 1291 passed (1290+1,
enumerated), 475 deselected (unchanged). Scope fence: only
`flexicon/code/FLExProject.py`, `flexicon/code/undoable_operation.py`, and
`tests/operations/test_issue243_closeproject_probe.py` touched by this
task; `test_abort_session_live.py` and `test_transaction_honesty.py`
carry only pre-existing T8b diffs, confirmed by no `Edit` call against
either this cycle. `CHANGELOG.md`/`spec.md`/`tasks.md`/`QUEUE.md`/`docs/`
untouched.

Evidence: `specs/243-closeproject-save-guard/evidence/live-t7-loud-close.md`.

**PASS.**
