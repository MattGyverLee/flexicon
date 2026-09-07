# Live evidence -- T1: lcm_casting._interface_cache feature-structure entries

**Task:** T1 (spec feature-structure-sync-gap, decision D3)
**Date:** 2026-09-07
**Project:** Ngoreme FLEx (read-only, `writeEnabled=False`); no writes performed.

## Exact commands

```
python -m pytest tests -m "not requires_live_project" -q
```
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_owner_cast_pattern.py -m requires_live_project -q
python -m pytest tests/operations/test_natural_classes.py tests/operations/test_natural_class_feature_sync.py tests/operations/test_phonemes.py -m requires_live_project -q
python -m pytest tests/contract/test_lcm_contract.py -m "not requires_live_project" -q
```

## run_mode

`tests/live_status.json` after the live run:
```json
"run_mode": "live",
"run_timestamp": "2026-09-07T06:15:14Z"
```
Confirms this was a real FieldWorks/pythonnet session (`FLExInitialize()` completed,
`[OK] Loaded 59/59 operations classes`), not a mock-mode degradation.

## Pre-state / post-state read back from the LCM

For each of the 9 ClassNames added to `_interface_cache`, an object was located live in
Ngoreme FLEx, re-fetched via `project.Object(hvo)` (guaranteed bare `ICmObject`, matching
the C2 HVO-path contract), then passed through `cast_to_concrete()`. Both the PRE (base
view) and POST (cast result) states were read back from the live object -- not asserted
from the value passed in.

| ClassName | Located via | PRE: `hasattr(project.Object(hvo), <attr>)` | POST: `hasattr(cast_to_concrete(...), <attr>)` | `isinstance(cast, <interface>)` |
|---|---|---|---|---|
| PartOfSpeech | `project.POS.GetAll()` | False (`DefaultFeaturesOA`) | True | True |
| PhPhoneme | `project.Phonemes.GetAll()` | False (`FeaturesOA`) | True | True |
| PhNCFeatures | `project.NaturalClasses.GetAll()` | False (`FeaturesOA`) | True | True |
| PhNCSegments | `project.NaturalClasses.GetAll()` | False (`SegmentsRC`) | True | True |
| FsComplexFeature | `project.InflectionFeatures.FeatureGetAll()` | False (`DefaultOA`) | True | True |
| FsFeatStruc | live `MoStemMsa.MsFeaturesOA` scan | False (`FeatureSpecsOC`) | True | True |
| FsComplexValue | nested `FeatureSpecsOC` scan (majority nested shape, per cycle-1 probe) | False (`ValueOA`) | True | True |
| FsClosedValue | `FeatureSpecsOC` scan | False (`ValueRA`) | True | True |
| PosFeatures | -- | -- | -- | SKIPPED: no live instance/interface located (see finding below) |

Console output (`-s`):
```
[T1] Exercised base-interface-view cast for: ['PartOfSpeech', 'PhPhoneme', 'PhNCFeatures', 'PhNCSegments', 'FsComplexFeature', 'FsFeatStruc', 'FsComplexValue', 'FsClosedValue']
[T1] Skipped (see reasons): ['PosFeatures (interface not present in this LCM version)']
```

## Finding: `IPosFeatures` confirmed absent from this LCM version

`tests/contract/test_lcm_contract.py::TestLiveContractVerification` (mode 2, live
liblcm introspection via `generate_lcm_snapshot.py`, gated by `requires_liblcm` /
`clr.AddReference("SIL.LCModel")`, distinct from `requires_live_project`) reported,
before the `IPosFeatures` handling was hardened:

```
Failed: 1 types not found in liblcm:
  - IPosFeatures
```

This is real live introspection against the installed `SIL.LCModel` assembly, not a
snapshot. It confirms `IPosFeatures` does not exist in this environment's LCM version.
`lcm_casting.py` now hardcodes `IPosFeatures = None` (no import attempt), following the
existing `IPhReduplicationRule` precedent, so the cache entry degrades to absent rather
than raising or polluting the static-contract governance test. See cycle2 report for
the full writeup and the `IFsComplexValue` baseline update this also required.

## Pass/fail

- Offline suite (`-m "not requires_live_project"`): **1277 passed**, 0 failed.
- `test_owner_cast_pattern.py` live (includes the new T1 regression test): **4 passed**,
  0 failed.
- NC/Phoneme live suite: **34 passed, 1 failed**. The 1 failure
  (`test_apply_raises_on_type_mismatch_segments_target`) is a **pre-existing** defect
  in `NaturalClassOperations.py:1270`, confirmed present identically on the pre-T1
  baseline via `git stash` + re-run (same `AttributeError: 'ICmObject' object has no
  attribute 'Name'`, same test, both before and after this change). **Not caused by
  T1** -- see cycle2 report finding.
- `test_lcm_contract.py` (offline mode): **22 passed**, 0 failed.

**Overall: PASS**, with the one pre-existing, unrelated failure noted and not silently
hidden.
