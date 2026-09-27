# Live verification evidence -- issue #557 follow-up (C4 `specs` envelope vs bare complex feature named `specs`)

## Change

`InflectionFeatureOperations.__DescribeSpecLevel`
(`flexicon/code/Grammar/InflectionFeatureOperations.py`): the C4 sync
envelope is now detected by metadata + shape (`"TypeGuid" in spec` and
all keys in `{"TypeGuid", "Guid", "specs"}` with `specs` a dict) via a
new `__IsC4Envelope` helper, instead of by the `"specs"` member alone.
A bare complex feature named `specs` now keeps its label and nesting:
`DescribeFeatStruc({"specs": {"number": "plural"}})` returns
`[specs: [number: plural]]` (was `[number: plural]`). Read-only,
display-only; no write path touched.

Regression tests added in `tests/operations/test_describe_featstruc.py`:
`test_bare_complex_feature_named_specs_keeps_label` and
`test_c4_envelope_holding_specs_named_feature`.

## Commands run

```
python -m pytest tests/operations/test_describe_featstruc.py -q -m "not requires_live_project"
```
Result: **22 passed** (20 existing + 2 new).

```
python -m pytest -m "not requires_live_project" -q
```
Result: **2556 passed**, 1052 deselected, 0 failed.

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_describe_featstruc_live.py -m requires_live_project -q
```
Result: **2 passed in 5.29s**. `tests/live_status.json`:
`"run_mode": "live"`, `"run_timestamp": "2026-09-27T03:47:41Z"`.

## What the live test checked

Project: `sena3_sandbox` (a fresh tempdir copy of the Sena 3 `.fwbackup`).
Nothing was written (pre-state = post-state; read-only change).

The existing live oracle test renders every non-empty MSA feature
structure in Sena 3 (719 structures, incl. nested `IFsComplexValue`
levels) three ways (GUID spec, owner, `IFsFeatStruc`) against an
independent LCM-walking oracle -- this exercises the new
`__IsC4Envelope` gate on real C4 envelopes at every level and confirms
no genuine envelope is misclassified as a bare spec.

The new `specs`-named-feature behavior itself is covered offline only:
Sena 3 has no complex feature literally named `specs`, so no live
oracle exists for that shape; the offline tests pin the specified
`[specs: [number: plural]]` rendering.

## Verdict

PASS (live for C4-envelope handling; offline for the new `specs`-label case).
