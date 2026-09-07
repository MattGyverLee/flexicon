# T9 -- fail-open comment fix + missing coverage, evidence (cycle 9)

## Scope

`flexicon/code/FLExProject.py` (comment only, zero executable change) and
`tests/operations/test_issue243_closeproject_probe.py` (one new offline
test). No other file touched.

## Predictions (stated BEFORE running, per C28 forward rule)

- `tests/operations/test_issue243_closeproject_probe.py -m requires_live_project --collect-only`: 11 tests.
- `tests/operations/test_abort_session_live.py -m requires_live_project --collect-only`: 12 tests.
- Live gate: 11/11 and 12/12 passed, `tests/live_status.json` `"run_mode": "live"`.
- Offline suite (`tests -m "not requires_live_project"`): baseline was
  1291 passed / 475 deselected. My one new test is NOT marked
  `requires_live_project`, so it lands directly in the passed bucket:
  predicted **1292 passed, 475 deselected (unchanged)**. Note: the
  dispatch brief stated "475 -> 476"; that is not how deselection counting
  works for a non-live-marked new test, so this report's own prediction
  (475 unchanged) is what is checked below, per the "if they differ, say
  so" instruction.

## Commands and results

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project --collect-only -q
11/13 tests collected (2 deselected)
```

```
$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project --collect-only -q
12 tests collected
```
Both match prediction.

```
$ python -m pytest tests -m "not requires_live_project" -q
1292 passed, 475 deselected, 17 warnings
```
Passed count matches prediction (1291 -> 1292). Deselected count matches
this report's own prediction (475 unchanged) and DIFFERS from the dispatch
brief's stated "475 -> 476" -- reporting the actual measurement, not
adjusting it to match the brief.

Mid-run finding: the initial (longer) comment draft pushed the
`save_body` source-slice window in `tests/test_transaction_honesty.py`
(`source[save_idx:save_idx+6000]`, fixed at 6000 by C26/addendum-D) from a
baseline distance of ~5240 chars to 6589, one file OUTSIDE this task's
scope fence, so it was not editable to fix. Comment was rewritten more
compactly (measured distance now 5735, 265-char margin) instead of
touching that file. `git diff --stat` confirms only the two in-scope
files changed.

```
$ $env:FLEXLIBS_REQUIRE_LIVE = "1"
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q
11 passed, 2 deselected, 1 warning in 12.54s

$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project -q
12 passed, 21 warnings in 8.49s
```
Both match prediction (11/11, 12/12).

`tests/live_status.json` -> `"run_mode": "live"` (line 119). Confirmed
live, not mock.

## Pass/fail

PASS. All predictions confirmed except the offline-suite deselected count,
where the dispatch brief's stated transition ("475 -> 476") does not match
how a non-live-marked new test affects collection; the measured value
(475, unchanged) is reported as the actual result per instruction.
