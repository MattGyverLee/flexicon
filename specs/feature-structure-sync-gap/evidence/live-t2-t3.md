# Live verification -- T2 (`_ResolveFeatureStrucOwner`) + T3 (`_GetFeatureStruc`, `_ResolveFsByGuid`)

**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup` -- the
real Target was never opened) for all write-path coverage;
`sena3_sandbox` (tempdir copy of the Sena 3 `.fwbackup`) for the
read-only nesting-frequency report.
**New test file:** `tests/operations/test_feature_struc_resolver.py`
(16 live tests + 13 offline tests).

## Commands (exact)

Offline suite first, to confirm the additive changes don't regress anything
without touching live LCM:

```
python -m pytest tests -m "not requires_live_project" -q
```
Result: **1290 passed** (1277 pre-existing + 13 new offline tests in this
file), 464 deselected.

Live run, fail-loud flag set:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_feature_struc_resolver.py -m requires_live_project -q -s
```
Result: **16 passed**, 13 deselected (the offline tests in the same file,
correctly skipped by `-m requires_live_project`).

Zero-delta regression check (existing NC/Phoneme/T1 live tests, unchanged
by this task):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_owner_cast_pattern.py::TestFeatureStructOwnerCastT1 tests/operations/test_natural_class_feature_sync.py tests/operations/test_issue251_252_256_feature_struct_probe.py -m requires_live_project -q
```
Result: **9 passed**, 14 deselected. No behavioural change to any existing
caller.

## run_mode

`tests/live_status.json` after the T2/T3 run:
```
"run_mode": "live",
"run_timestamp": "2026-09-07T06:46:53Z",
```
Confirmed live, not mock -- FieldWorks assemblies loaded via
`clr.AddReference("SIL.LCModel")` per the session fixture's own log
(`[OK] SIL assemblies loaded`, `[OK] Loaded 59/59 operations classes`).

## Pre/post values re-queried from the LCM (not asserted against the value passed in)

### T2 -- `_ResolveFeatureStrucOwner`

For every in-scope C1 row, the test (a) creates the object live via the
normal Operations API, (b) discovers its `.Hvo`, (c) re-fetches it via a
fresh `project.Object(hvo)` call (guaranteed bare `ICmObject` per C2 --
never the factory-fresh concrete return value), and (d) calls
`sandbox.MSA._ResolveFeatureStrucOwner(bare_obj, slot=...)` on that
re-fetched object. Post-state assertions:

| ClassName | slot | resolved prop_name | `hasattr(concrete, prop_name)` post-cast |
|---|---|---|---|
| MoStemMsa | -- | MsFeaturesOA | True |
| MoInflAffMsa | -- | InflFeatsOA | True |
| MoDerivAffMsa | From | FromMsFeaturesOA | True |
| MoDerivAffMsa | To | ToMsFeaturesOA | True |
| PartOfSpeech | Default | DefaultFeaturesOA | True |
| PartOfSpeech | InherFeatVal | InherFeatValOA | True |
| MoAffixAllomorph | -- | MsEnvFeaturesOA | True |
| PhNCFeatures | -- | FeaturesOA | True |
| PhPhoneme | -- | FeaturesOA | True |
| WfiAnalysis | -- | MsFeaturesOA | True |

Also live-verified: `slot=` ignored on a single-row owner (MoStemMsa with
`slot="TotallyIrrelevant"`) does not raise; a real live
`MoUnclassifiedAffixMsa` instance (excluded ClassName) raises
`FP_ParameterError` naming `"MoUnclassifiedAffixMsa"` in the message.

### T3 -- `_GetFeatureStruc` nested round trip

Built with RAW `IFsFeatStrucFactory` / `IFsComplexValueFactory` /
`IFsClosedValueFactory` calls (no `MakeFeatStruc`), ownership-first at
every level, on a fresh `MoStemMsa.MsFeaturesOA`:

- Write-time GUIDs recorded: `complex_feat.Guid`, `closed_feat.Guid`,
  `feat_value.Guid`, `inner_type.Guid`, `nested_struct.Guid`.
- Post-state: a brand-new `project.Object(stem.Hvo)` fetch ->
  `_ResolveFeatureStrucOwner` -> `getattr(concrete, "MsFeaturesOA")` ->
  `_GetFeatureStruc(...)`.
- Result:
  - `result["TypeGuid"] is None` (outer `TypeRA` never set -- matches the
    live shape from `evidence/live-cycle1-probe.md`: only the outer
    `TypeRA` is null).
  - `"Guid" not in result` (top level omits it, per C4).
  - `result["specs"]` has exactly one key: the write-time
    `complex_feat.Guid`.
  - The nested dict's `"TypeGuid"` == write-time `inner_type.Guid`;
    `"Guid"` == write-time `nested_struct.Guid`; `"specs"` ==
    `{closed_feat.Guid: feat_value.Guid}` (write-time values).

All five re-read values matched their write-time counterparts exactly --
this is a genuine LCM read-back, not an assertion on the value passed in.

### T3 -- empty-but-present struct

An `IFsFeatStruc` attached to `MoInflAffMsa.InflFeatsOA` with zero
`FeatureSpecsOC` entries. Re-fetched via a fresh `project.Object(hvo)` and
serialized: `{"TypeGuid": None, "specs": {}}` -- confirmed NOT `None`.

### T3 -- `_ResolveFsByGuid`

A real `IFsClosedFeature`'s GUID resolves to an object whose `.Guid`
matches; the all-zero GUID `00000000-0000-0000-0000-000000000000` returns
`None` (both with and without a `kind=` label) rather than raising.

### Section D -- Sena 3 natural-nesting measurement (informational)

```
[T3][Sena 3] non-null MSA feature structs: 719; naturally nested (contains an IFsComplexValue spec): 717
```
**717/719 (99.7%) of Sena 3's populated MSA feature structures are
naturally nested.** This corroborates the cycle-1 Ngoreme finding
(799/820 nested) on a second, independently-populated project, and is
relevant to the open T9b measurement question the spec records for NC/
Phoneme (a different owner family -- this number is MSA-only, gathered via
`BaseOperations._GetFeatureStruc` itself so it reflects exactly what T3
produces).

## Zero-delta confirmation for existing callers

- No file under `NaturalClassOperations.py`, `PhonemeOperations.py`,
  `PhonFeatureOperations.py`, `InflectionFeatureOperations.py`,
  `MSAOperations.py`, `POSOperations.py`, or `AllomorphOperations.py` was
  modified (`git status` shows only `BaseOperations.py`,
  `Shared/lcm_constants.py`, and the new test file changed under
  `flexicon/`).
- `NaturalClassOperations.__ApplyFeatures`'s private `__ResolveByGuid` is
  untouched -- `tests/operations/test_natural_class_feature_sync.py`'s
  five `inspect.getsource` shape assertions (including the
  `src.index("feat_obj = self.__ResolveByGuid")` check at ~:145) still
  pass, live-verified above.
- Offline suite count: 1277 (pre-existing, unchanged) + 13 (new, this
  task) = 1290, all green.
