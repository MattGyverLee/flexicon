# T7 -- the C23-recut loudness log (evidence)

Scope: `flexicon/code/FLExProject.py` (`CloseProject()` only),
`flexicon/code/undoable_operation.py` (docstring only, C25 caveat),
`tests/operations/test_issue243_closeproject_probe.py`. `SaveChanges()`,
`CHANGELOG.md`, `spec.md`, `tasks.md`, `QUEUE.md`, `docs/` untouched by this
task (owned by a parallel `/lex-doc` task this cycle).

## Scope fence check

```
$ git diff --stat -- flexicon/code/FLExProject.py flexicon/code/undoable_operation.py tests/operations/test_issue243_closeproject_probe.py
 flexicon/code/FLExProject.py                       |  242 ++-
 flexicon/code/undoable_operation.py                |   13 +
 tests/operations/test_issue243_closeproject_probe.py | 1112 ++++++++++++++---
 3 files changed, 1181 insertions(+), 186 deletions(-)
```

Note: these three files carried pre-existing UNCOMMITTED T8b changes before
this task started (nothing in this feature has been committed yet), so the
diff above is not isolable to T7 alone by `git diff` -- same caveat T8b's
own evidence file recorded for other files. `test_abort_session_live.py`
and `test_transaction_honesty.py` were NOT touched by this task (no `Edit`
call against either); their working-tree diffs are 100% pre-existing T8b
work, confirmed by `git status --short` before this task began.

## Work done

1. `CloseProject()`'s Phase-1 `else:` branch (`HasOpenSessionTask()` reads
   `False`) now logs at **ERROR**, not `debug`. Message names the anomaly
   ("unreachable by construction unless the session envelope was already
   ended before `CloseProject()` was entered"), states plainly that
   `usm.Save()` proceeds anyway, and asserts nothing about data loss. The
   withdrawn `FP_ProjectError` raise (C23) was never reintroduced.
2. Detector unchanged (C18): the branch entry itself is the PRIMARY
   detector; a pre-`Save()` `HasUnsavedChanges` read is logged as a raw
   diagnostic value only, wrapped in its own `try/except` so a read
   failure can't break the log line, and gates nothing.
3. `Dispose()`/`del self.project` moved into a `finally` (C15) wrapping
   the whole write/save block, so they always run, including when
   `usm.Save()` itself raises.
4. `undoable_operation.py`'s `__exit__` docstring gained the dated C25
   caveat citing T8b's P-11 measurement verbatim (25/25 in-memory, 25/25
   after close-and-reopen, despite `set_RollBack(True)`+`Dispose()`
   confirmed run) -- object creation only, no claim about property
   modification or deletion. Zero executable-line change.
5. Checked `transaction.py` for a surviving rollback-discards claim per
   the task brief -- **found one, reported, not edited**: lines ~146-153
   assert "`Dispose()` then rolls back EVERY unit of work... a created POS
   vanished on clean exit" under the `.RollBack = False` assignment-bug
   scenario. This is a DIFFERENT measured scenario (the pythonnet
   property-assignment bug, not a normal escaping exception) from P-11's
   finding, so it is not directly contradicted, but a future reader
   reconciling the two should know both exist. Not touched, per the task
   brief's explicit instruction.

## Tests added/changed (all in `test_issue243_closeproject_probe.py`)

- Module-level `pytestmark = pytest.mark.requires_live_project` replaced
  with `@pytest.mark.requires_live_project` on each of the 11 pre-existing
  test functions individually (mechanical, zero behaviour change), so a
  new **offline** test can coexist in the same file without inheriting
  the live marker.
- `test_p4_control_run_normal_close`: added `caplog` fixture; asserts the
  T7 anomaly ERROR record does NOT fire (this run's envelope is ended by
  `CloseProject()` itself, the "if" branch).
- `test_p5_save_before_forced_end`: added `caplog` fixture; asserts
  exactly one ERROR record fires, at ERROR level, containing "unreachable
  by construction" and "usm.Save()"/"proceeding", and NOT containing
  "lost" or "nothing pending to save".
- `test_c15_dispose_runs_in_finally_even_when_save_raises` (**NEW,
  OFFLINE/MOCK, not live** -- no `requires_live_project` marker):
  constructs a bare `FLExProject`, stubs `self.project`/`ObjectRepository`,
  forces `usm.Save()` to raise, asserts `Dispose()` still runs and
  `self.project` is still deleted, and the original exception still
  propagates. This is the only way to isolate C15's finally guarantee --
  no live route reaches a raising `usm.Save()`.

## Commands, `--collect-only` derivations

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project --collect-only -q
11/12 tests collected (1 deselected) in 0.24s
```
(11 live, unchanged from T8b; the 1 deselected is the new offline mock test.)

```
$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project --collect-only -q
12 tests collected in 0.93s
```
(unchanged from T8b -- this task did not touch this file.)

## Live runs (`FLEXLIBS_REQUIRE_LIVE=1`)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
11 passed, 1 deselected, 1 warning in 12.63s

$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project -q
12 passed, 21 warnings in 6.95s
```

`tests/live_status.json`:
```
"run_mode": "live",
"run_timestamp": "2026-09-07T17:01:58Z"
```

## P-4 and P-5 `[PROBE]` lines, verbatim (including the new ERROR log line)

```
[PROBE][P4] created 25 entries with prefix 'TEST_p4_'
[PROBE][P4] anomaly ERROR records logged (expected 0): 0
[PROBE][P4] TEST_ entries surviving after normal CloseProject, re-read from LCM: 25 / 25
[PROBE][P4] VERDICT: expected 25 survivors; observed 25

[PROBE][P5] created 25 entries with prefix 'TEST_p5_'
[PROBE][P5] CurrentDepth before SaveChanges(): 1
[PROBE][P5] CurrentDepth after SaveChanges() attempt: 1
[PROBE][P5] SaveChanges() now refuses BEFORE usm.Save() (T8b): FP_TransactionError: SaveChanges() refused: CurrentDepth is 1 (the session-long non-undoable envelope opened by OpenProject(undoable=False) is still open). usm.Save() was NOT attempted, so this refusal itself discarded nothing -- your pending changes are intact in memory and will be written to disk by CloseProject(). Calling through here would instead have discarded the session's pending changes (measured 0/25 survivors when this guard did not exist -- spec.md P-5/P-7/P-10-C). Mid-session saving requires opening the project with undoable=True instead.
[PROBE][P5] anomaly ERROR records logged (expected 1): 1
[PROBE][P5] ERROR record: level=ERROR message='CloseProject: HasOpenSessionTask() read False inside Phase 1 (writeEnabled and not _undoable) -- unreachable by construction unless the session envelope was already ended before CloseProject() was entered. Skipping EndNonUndoableTask() and proceeding to usm.Save() below regardless (pre-Save() HasUnsavedChanges=True, a diagnostic value only -- spec.md C18 -- not proof of what is or is not pending).'
[PROBE][P5] TEST_ entries surviving, re-read from LCM: 25 / 25
[PROBE][P5] GO/NO-GO VERDICT (T8b guard, measured not assumed): 25/25 survived -- MATCHES the T8b prediction: SaveChanges()'s guard never touched the envelope or the change set, the manual End committed it normally, and CloseProject() persisted it at a legal depth.
```

**Pre-state -> post-state, re-read from the LCM (not the values passed
in):** both P-4 and P-5 create 25 `TEST_` entries, then re-open the SAME
`.fwdata` read-only and re-count with a fresh `FLExProject` -- P-4: 25/25,
P-5: 25/25. Neither is asserting on the in-process value; both counts come
from `_count_prefixed_entries()` against a freshly reopened project.

## Offline baseline

```
$ unset FLEXLIBS_REQUIRE_LIVE
$ python -m pytest tests -m "not requires_live_project" -q
1291 passed, 475 deselected, 17 warnings in 11.52s
```

**1291 passed** = 1290 (frozen baseline through T8b) + 1 (the new
`test_c15_dispose_runs_in_finally_even_when_save_raises`, MOCK/OFFLINE,
not live verification). **Deselected unchanged at 475** -- the 11
pre-existing live tests kept their marker individually, nothing was
removed from the live set.

## Mock-only C15 test, run in isolation (labelled explicitly as NOT live)

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m "not requires_live_project" -q
1 passed, 11 deselected, 1 warning in 1.13s
```

This is a MOCK pass and is not presented as live verification of anything
beyond the `finally` control-flow structure itself.

## PASS/FAIL line

**PASS.** All 11 live probe tests green, all 12 `test_abort_session_live.py`
live tests green (unaffected), `run_mode: live` confirmed, offline baseline
1291 (1290+1, enumerated), ERROR record confirmed firing exactly once on
the one live route into the anomaly branch (P-5) and zero times on the
normal-close control (P-4), message content confirmed to name the anomaly,
state `usm.Save()` proceeds, and NOT assert data loss or "nothing pending
to save". C15's `finally` guarantee confirmed by a labelled offline mock
test. No prediction was contradicted this cycle -- the only correction
needed was to my own test's overly strict "lost" substring check against
my own log message (fixed by rewording the message to drop the word
entirely, not by loosening the test).
