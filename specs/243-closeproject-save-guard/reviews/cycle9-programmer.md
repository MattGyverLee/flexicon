# Cycle 9 -- Programmer report -- T9 (fail-open comment fix + missing coverage)

## T9a -- comment rewrite (FLExProject.py, zero executable change)

Rewrote the `except Exception` comment at `SaveChanges()` (now ~843-855,
shifted from 843-859 by a prior spurt's changes) to state: (1) the catch
is `except Exception`, not narrowed to `FP_ProjectError` -- ANY depth-read
exception fails open, per C21's "unreadable depth is never grounds to
refuse a save"; (2) the measured-safe case is by CODE INSPECTION at
cycle-8 QC, not a live probe -- when `self.project` is absent,
`ObjectRepository()` shares that dependency and raises before
`usm.Save()`; (3) the un-measured residual, stated per C10 discipline: an
unknown depth-read failure mode with `ObjectRepository()`/`usm.Save()`
both still succeeding at depth > 0 would proceed blind into #243's
incident -- not claimed safe, not claimed a bug. No "lost"/loss-claim
vocabulary used. `git diff` confirms zero executable-line change.

**Mid-task correction:** my first draft (accurate but verbose) pushed
`test_transaction_honesty.py`'s pinned `save_body` 6000-char source-slice
window (C26 addendum D) from ~5240 to 6589 chars, breaking that OFFLINE
test -- a file outside this task's scope fence. Rewrote the comment more
compactly (measured distance now 5735, 265-char margin) rather than touch
that file. Verified via `git diff --stat`: only the two in-scope files
changed.

## T9b -- new offline test

Added `test_savechanges_failopen_depth_read_raises_reaches_usm_save` to
`test_issue243_closeproject_probe.py` (no `requires_live_project` mark,
per file convention). Patches `FLExProject.CurrentDepth` (PropertyMock) to
raise `RuntimeError` (deliberately not `FP_ProjectError`), asserts: (a) a
WARNING naming "could not evaluate the issue #243 depth" and containing
"RuntimeError" is emitted; (b) `SaveChanges()` does not raise; (c)
`fake_usm.Save.assert_called_once()`.

## Verification (evidence: `evidence/live-t9-failopen-coverage.md`)

- Collect-only: probe file 11 live tests, abort-session file 12 -- both
  match prediction.
- Live gate (`FLEXLIBS_REQUIRE_LIVE=1`): 11 passed / 12 passed. Both
  match prediction. `tests/live_status.json` -> `"run_mode": "live"`.
- Offline suite: 1292 passed, 475 deselected (unchanged). Passed count
  matches the predicted 1291->1292. Deselected count differs from the
  dispatch brief's stated "475->476" -- a non-live-marked new test lands
  in the passed bucket, not the deselected one; reporting the actual
  measurement (475, unchanged) per the "don't adjust the prediction"
  instruction, with the reasoning stated in the evidence file.

## Scope fence

Confirmed via `git status`/`git diff --stat`: only
`flexicon/code/FLExProject.py` and
`tests/operations/test_issue243_closeproject_probe.py` were modified by
this task. spec.md/tasks.md/STATUS.md/QUEUE.md show as modified in
`git status` but were already changed by a prior cycle's doc agent before
this task started -- not touched here.
