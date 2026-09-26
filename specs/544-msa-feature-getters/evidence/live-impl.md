# Live verification evidence -- issue #544 (MSA feature-structure getters)

## Commands run

```
python -m pytest -m "not requires_live_project" -q
```
Result: 2515 passed, 4 pre-existing failures (unrelated to this change,
in `tests/operations/test_morphrule_duplicate_deep.py`; confirmed
present on a clean `origin/main` checkout via `git stash` before this
change was applied).

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_msa_feature_getters_live.py -m requires_live_project -q
```
Result: **5 passed**, `run_mode: "live"` in `tests/live_status.json`
(`by_class.MSAOperations.read.status == "pass"`, all 5 tests listed).

## Correction from cycle 1

Cycle 1 reported this as blocked ("no SIL.LCModel, no fixture"). That
was wrong: the fixture is git-ignored and had simply not been copied
into this worktree yet ("No module named SIL" before flexicon's own
FLEx init is normal, not a missing-install signal). The coordinator
placed `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup` and the session
fixture (`tests/flex_plugin.py`) loads the SIL assemblies itself before
tests run. Superseding the cycle-1 "FAIL: unverified" verdict with the
real live run below.

## Bug found by the first live run, and its fix

The first live run of
`TestStemFeaturesRoundTripLive::test_get_stem_features_round_trips_through_make_feat_struc`
failed:

```
tests\operations\test_msa_feature_getters_live.py:117: nested = list(complex_spec.ValueOA.FeatureSpecsOC)
AttributeError: 'IFsAbstractStructure' object has no attribute 'FeatureSpecsOC'
```

**Investigated per Category 8 (docs/API_ISSUES_CATEGORIZED.md): confirmed
this is a test-assertion bug, not a library bug.**

- `BaseOperations._GetFeatureStruc` (the library method the new
  getters build on) already performs the required
  `IFsFeatStruc(nested_value_oa)` cast at the top of its own recursive
  call before ever reading `FeatureSpecsOC` (`BaseOperations.py:2166`
  onward, and the explicit comment at the `FsComplexValue` branch,
  `BaseOperations.py:2201-2204`, documents exactly this rule).
- `MSAOperations.__C4ToFeatStrucSpec` (the new converter) never touches
  a raw LCM object at all -- it only walks the already-serialized C4
  dict `_GetFeatureStruc` returns (plain `dict.items()`/`isinstance`
  checks). There is no code path in the converter or the five new
  getters that reads `ValueOA` directly.
- The `AttributeError` came from this test file's own re-read
  assertion (`test_msa_feature_getters_live.py`, `TestStemFeaturesRoundTripLive`),
  which read `complex_spec.ValueOA.FeatureSpecsOC` without the
  `IFsFeatStruc(...)` cast pythonnet requires -- the exact same mistake
  the docstring at `BaseOperations.py:2201` warns against, just
  committed in test code instead of library code.

**Fix applied**: added the missing `IFsFeatStruc(complex_spec.ValueOA)`
cast in the test (`tests/operations/test_msa_feature_getters_live.py`),
with a comment explaining why, plus a new offline regression test,
`TestC4ToFeatStrucSpec.test_converter_never_touches_a_raw_lcm_object`
(`tests/operations/test_msa_feature_getters.py`), which pins that the
converter operates purely on dict keys/values and never attribute-
accesses a nested value -- so this bug shape cannot silently reappear
in library code. No library code changed as a result of this
investigation; `flexicon/code/BaseOperations.py` and
`flexicon/code/Lexicon/MSAOperations.py` are unchanged from cycle 1.

## Pre-state / post-state read back from the LCM (real values, one live run)

Captured by temporarily instrumenting
`TestStemFeaturesRoundTripLive::test_get_stem_features_round_trips_through_make_feat_struc`
with `print()` calls (reverted afterward; final committed test file has
no prints) and running
`pytest tests/operations/test_msa_feature_getters_live.py::TestStemFeaturesRoundTripLive -m requires_live_project -q -s`
against the Sena 3 sandbox:

```
PRE  stem1.MsFeaturesOA attached=True guid=d4705f42-d93c-416b-a8d1-da20f2d6b5ce
agreement_feat.Guid=64020140-a11f-4ab9-93b4-998aa13fc212
number_feat.Guid=378c0109-da3d-4d40-93cc-7b4355590d82
sg_val.Guid=1c083a78-456f-4ae1-a11f-f4c03f32fb4e

GetStemFeatures(stem1_hvo) =
  {'64020140-a11f-4ab9-93b4-998aa13fc212':
     {'378c0109-da3d-4d40-93cc-7b4355590d82': '1c083a78-456f-4ae1-a11f-f4c03f32fb4e'}}

POST stem2.MsFeaturesOA attached=True guid=8675f578-1dfe-45d6-a129-9fc80d761699
  (a DIFFERENT struct GUID from stem1's -- a fresh struct was created by
  the round-trip MakeFeatStruc call, on a SECOND, independent MSA)

GetStemFeatures(stem2_hvo) =
  {'64020140-a11f-4ab9-93b4-998aa13fc212':
     {'378c0109-da3d-4d40-93cc-7b4355590d82': '1c083a78-456f-4ae1-a11f-f4c03f32fb4e'}}
```

`GetStemFeatures(stem1_hvo) == GetStemFeatures(stem2_hvo)` -- the
getter's own output, fed straight back into
`MakeFeatStruc(spec_out, owner=stem2)`, reproduced an equivalent
(same feature/value GUIDs) feature structure on a completely
independent MSA, re-read fresh from the LCM after the round-trip. This
is the round-trip issue #544 asked for.

The other four live tests (`GetInflAffFeatures`, `GetDerivFromFeatures`
+ `GetDerivToFeatures` together, the `MoUnclassifiedAffixMsa`/null-
`MsFeaturesOA` `None` cases, and the read-only sweep over real Sena 3
MSAs) passed the same way -- asserting `spec_out == {featGuid: valGuid}`
against GUIDs read directly off the LCM feature/value objects, then
re-applying and re-reading a second time -- without needing separate
instrumented capture (their assertions themselves compare real,
LCM-sourced GUID strings).

## PASS line

**PASS.** `run_mode: "live"` confirmed in `tests/live_status.json`;
5/5 live tests pass against the Sena 3 sandbox; offline suite (2515
non-live tests, unrelated pre-existing failures excluded) passes;
round-trip proven with real GUIDs read back from the LCM before and
after `MakeFeatStruc(getter_output, owner=<second, independent MSA>)`.

All live writes went through `sena3_sandbox` only (a tempdir copy of
`tests/fixtures/Sena 3 2026-06-09 1645.fwbackup`); `Target` was never
opened by these tests. The `.fwbackup` fixture is git-ignored and was
not committed.
