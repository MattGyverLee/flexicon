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

(filled in after the live run, second commit)

## OFFLINE DELTA

(filled in after the live run, second commit)
