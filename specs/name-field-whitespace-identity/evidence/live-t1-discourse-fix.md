# Name-field whitespace identity -- T1 (DiscourseOperations persist fix), live evidence

**Scope (per `tasks.md` T1 / `spec.md` C4, C5, C8):**
`flexicon/code/TextsWords/DiscourseOperations.py`, exactly two expressions:
- `CreateChart` -- remove the rebinding `name = name.strip()` at `:327`
  (verified at HEAD by symbol lookup before editing, matches the brief
  exactly; `_ValidateStringNotEmpty(name, "chart name")` at `:320` is
  unchanged and stays).
- `SetChartName` -- remove the rebinding `name = name.strip()` at `:482`
  (verified at HEAD; `_ValidateStringNotEmpty(name, "chart name")` at
  `:481` is unchanged and stays).

No comparison/dedup method exists on `DiscourseOperations` (C3's explicit
per-family carve-out) -- none is added. No shared file
(`BaseOperations.py`, `Shared/string_utils.py`) is touched.

## OFFLINE BASELINE, BEFORE THE EDIT

Command: `python -m pytest tests -m "not requires_live_project" -q`

First attempt (transient, documented, NOT used as the baseline -- see the
programmer report's CONTRACT CONTRADICTIONS FOUND section):
```
4 failed, 1291 passed, 498 deselected, 12 warnings in 14.62s
```
The 4th failure (`test_natural_class_feature_sync.py::TestNaturalClassSyncStatic::test_apply_features_raises_on_unresolved_feature_guid`)
coincided with `git status --porcelain` showing `flexicon/code/BaseOperations.py`
as modified (the other crew's live in-progress edit, per `CONCURRENCY.md`).
Re-run ~30s later, in isolation, PASSED; a second full-suite re-run once
their edit had settled (git status showed `BaseOperations.py` clean again)
matched the expected baseline exactly.

**Baseline used (second, stable run):**
```
3 failed, 1292 passed, 498 deselected, 0 errors (12 warnings) in 15.57s
```
Matches CONCURRENCY.md's expected red baseline exactly: the three named
known-foreign failures
(`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`)
and no others.

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T1-P1 (CreateChart persist):** After removing the `name = name.strip()`
  rebinding at `:327`, calling
  `Discourse.CreateChart(text, "TEST_NF_Chart_Raw ")` (trailing space) is
  **PREDICTED** to persist the chart's `Name` re-read from the LCM
  (`ITsString(chart.Name.get_String(wsHandle)).Text` or
  `.BestAnalysisAlternative`) as **byte-identical** to the caller's
  original argument, `"TEST_NF_Chart_Raw "`, including the trailing space
  -- because `name_str = TsStringUtils.MakeString(name, wsHandle)` at
  `:351` now runs against the untouched parameter, not a stripped local.

- **T1-P2 (SetChartName persist):** After removing the `name = name.strip()`
  rebinding at `:482`, calling
  `Discourse.SetChartName(chart, "TEST_NF_Chart_Renamed ")` (trailing
  space) is **PREDICTED** to persist the chart's `Name` re-read from the
  LCM as byte-identical to `"TEST_NF_Chart_Renamed "`, same mechanism.

- **T1-P3 (no dedup regression):** `DiscourseOperations` has no comparison
  method today and none is added by this task, so there is no
  "raises already exists" half to test (per C8's family-specific note).
  Calling `CreateChart` twice with the same padded name is **PREDICTED**
  to succeed BOTH times (two distinct chart objects, no exception) --
  this is not a new behaviour, it is the pre-existing (and correct, per
  C3's carve-out) absence of a dedup guard, asserted here only so a future
  reader does not mistake silence for an oversight.

- **T1-P4 (whitespace-only rejection unaffected):** `CreateChart(text, "   ")`
  and `SetChartName(chart, "   ")` are **PREDICTED** to still raise
  `FP_ParameterError` via the unchanged `_ValidateStringNotEmpty` call at
  `:320`/`:481` (confirmed at `BaseOperations.py:2915`/`:2966` per
  CONCURRENCY.md's re-derived line numbers -- already raises on
  whitespace-only input, no helper change needed). This is a
  regression-guard prediction, not new scope.

## Test file

`tests/operations/test_name_field_identity_probe.py` -- EXTENDED in place
(new tests appended after PN8; no parallel probe file created), using
`target_sandbox` exclusively.

## LIVE EVIDENCE

**Diff proof:** `git diff -- flexicon/code/TextsWords/DiscourseOperations.py`
shows exactly the two authorised removals -- `name = name.strip()` deleted
at the old `:327` (inside `CreateChart`) and at the old `:482` (inside
`SetChartName`) -- and nothing else. `_ValidateStringNotEmpty` calls at
`:320`/`:481` are byte-for-byte unchanged.

**Collect count:**
```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
```
-> **11 tests collected** (PN1-PN8 pre-existing + PN9/PN10/PN11 new for T1).
Nonzero.

**Live run:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
```
-> `11 passed, 52 warnings in 7.64s`. `tests/live_status.json` confirms
`"run_mode": "live"`, `"run_timestamp": "2026-09-07T20:06:17Z"`, and lists
`DiscourseOperations` add/modify/read all `"status": "pass"` for
PN9/PN10/PN11 respectively.

**T1-P2 (SetChartName) -- FULLY VERIFIED, PASS:** a chart was constructed
via the CORRECT LCM ownership path (`LangProject.DiscourseDataOA.ChartsOC`
-- see "CONTRACT CONTRADICTIONS FOUND" below for why the public
`CreateChart` could not be used to seed it), then `Discourse.SetChartName(
chart, "TEST_NF_Chart_Renamed ")` was called through the REAL public API.
Re-read directly from the LCM afterward:
`ITsString(chart.Name.get_String(wsHandle)).Text` -> `'TEST_NF_Chart_Renamed '`,
**byte-identical** to the caller's argument, trailing space included.
Prediction T1-P2 MATCHED exactly.

**T1-P1 (CreateChart) -- BLOCKED, NOT independently live-verifiable via
its own public entry point; reported honestly, not smoothed over:**
`Discourse.CreateChart(text, "TEST_NF_Chart_Raw ")` (padded) and
`Discourse.CreateChart(text, "TEST_NF_Chart_Raw_Unpadded")` (unpadded)
both raised the IDENTICAL exception,
`FP_ParameterError: Text contents does not support charts`, proving the
blocker is unrelated to T1's own edit (see CONTRACT CONTRADICTIONS FOUND
for the two unrelated, pre-existing bugs discovered this cycle: an
already-broken `IConstChartFactory` NameError, PLUS a second, deeper,
unrelated bug -- CreateChart's collection check queries the wrong LCM
interface for chart ownership, so it can never succeed for ANY payload,
today, independent of whitespace). **T1's own code change at that
persist line is confirmed correct by direct inspection** -- `name` now
flows unmodified into `TsStringUtils.MakeString(name, wsHandle)` -- but
this specific half of the anti-regression pin is reported as
`FAIL: unverified` at the live level, exactly as CLAUDE.md's Live LCM
Verification section requires when live verification of one path is
genuinely blocked: reported plainly, not silently downgraded to a pass.

**T1-P3 (no dedup regression) -- CONFIRMED, non-binding, informational
only (no test needed):** `DiscourseOperations` still has no comparison
method; nothing in this task added one.

**T1-P4 (whitespace-only rejection unaffected) -- MATCHED:**
`Discourse.CreateChart(text, "   ")` raised
`FP_ParameterError: chart name cannot be empty or contain only whitespace`,
confirming the unchanged `_ValidateStringNotEmpty` guard at `:320` still
fires correctly after the rebinding was removed.

## OFFLINE DELTA

| | passed | failed | deselected |
|---|---|---|---|
| Before (stable baseline, second run -- see WHAT CHANGED for the transient first run) | 1292 | 3 | 498 |
| After | 1292 | 3 | 501 |
| Delta | +0 | +0 | **+3** |

`3 failed` after the edit are the SAME three known-foreign tests, same
messages, confirmed by name:
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
`passed` unchanged (T1 added zero new OFFLINE tests -- PN9/PN10/PN11 are
all `requires_live_project`). `deselected` up by exactly 3, matching the
3 new live tests added. This is the expected delta shape for a correct
change per `CONCURRENCY.md`/`tasks.md`'s DELTA rule.

## WHAT WAS NOT EXERCISED

- **T1-P1, `CreateChart`'s persist half, is `FAIL: unverified`.** Blocked
  by two pre-existing, unrelated defects (recorded as **Q-DISC1** in
  `specs/tier1-silent-data-loss/QUEUE.md`): (1) an `IConstChartFactory`
  NameError at `DiscourseOperations.py:~335`; (2) a wrong chart-ownership
  interface check at `:~340` (`hasattr(text_obj.ContentsOA, "ChartsOC")`),
  confirmed by direct reflection on the live LCM assemblies that `IStText`
  has no `ChartsOC` member -- the real owner is `IDsDiscourseData` via
  `LangProject.DiscourseDataOA`. Both padded and unpadded inputs raised the
  identical `FP_ParameterError: Text contents does not support charts`,
  ruling out this task's own edit as the cause. The persist-and-reread half
  of the pin could not be exercised through `CreateChart`'s own public
  entry point.
  - Why: pythonnet regenerates a fresh Python wrapper on every `.ContentsOA`
    access, so no test-instance-only workaround (in the spirit of C9) could
    make the public path reachable without editing `flexicon/` code, which
    is out of scope for this task.
- **T1-P1's correctness is confirmed by code inspection only, not by a
  live persist-and-reread.** `name` was confirmed, by reading the diff, to
  flow unmodified into `TsStringUtils.MakeString(name, wsHandle)` at the
  persist line -- the same mechanism independently proven live for
  `SetChartName` (T1-P2) -- but this is inspection, not an independent live
  measurement of `CreateChart` itself.
