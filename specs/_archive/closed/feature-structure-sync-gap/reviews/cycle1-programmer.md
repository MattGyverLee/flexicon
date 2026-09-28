# Phoneme Feature Sync Implementation Report (Task T9 / issue #253) -- REVISED

## Summary

T9's production implementation in `flexicon/code/Grammar/PhonemeOperations.py` is complete
and the offline test suite is green. A corrected test file
`tests/operations/test_phoneme_feature_sync_issue253.py` (9 offline / 2 live) pins the
contract. The live gate is NOT yet run -- that is cycle 2's job (mandatory
`FLEXLIBS_REQUIRE_LIVE=1`, target_sandbox).

## Changes made (production, PhonemeOperations.py)

1. **C2 -- HVO-path cast** (`__GetPhonemeObject`, :1314): the int-HVO branch now returns
   `IPhPhoneme(self.project.Object(phoneme_or_hvo))` instead of a bare ICmObject, so the
   feature-sync path always writes through a concrete view with `FeaturesOA`.
2. **C6 -- presence gate** (`ApplySyncableProperties`, :1476): the gate is now
   `if features or features_guid:` (key-presence, not truthiness). `FeaturesGuid` is
   extracted at :1463 as `props.get("FeaturesGuid")`; both `Features` and `FeaturesGuid`
   are POPPED into `base_props` exclusion before `super()`.
3. **Struct-GUID preservation**: `features_guid` is threaded through
   `__ApplyFeatures(phoneme, features, features_guid, on_unresolved="raise")` and passed
   as `struct_guid=features_guid` to `BaseOperations._ApplyFeatureStruc`.
4. **C7 policy flip**: the default is now `on_unresolved="raise"` (was `"skip"`),
   matching NaturalClassOperations. `on_unresolved="skip"` stays an explicit opt-in.

## Test file (9 offline + 2 live)

- Offline fake-object tests (pattern from test_issue252_pos_feature_sync.py):
  - C6 presence: empty-but-present `Features` with a real `FeaturesGuid` still triggers
    apply; guid-only (no `Features` key) triggers; neither key present never calls
    `_ApplyFeatureStruc`; feature keys popped before super; `None` item raises.
  - C7: default `on_unresolved="raise"` threads through the public surface; an
    unresolvable GUID surfaces as `FP_ParameterError` (through the `_ApplyFeatureStruc`
    seam, so the raise is the resolver's verdict, not an early bail).
  - C2: int-HVO path records exactly one `IPhPhoneme(...)` cast; object path passes
    through unchanged. Kill check: deleting the cast fails the first test.
- Live tests (`@pytest.mark.requires_live_project`, `target_sandbox`, `live_phase`
  markers):
  - valid spec round-trip via `ApplySyncableProperties`, struct-GUID preserved, specs
    re-read from a FRESH `IPhPhoneme(sandbox.Object(ph.Hvo))` fetch;
  - unresolvable feature GUID raises `FP_ParameterError` and leaves no partial spec.

## Offline verification (run this cycle)

`$env:FLEXLIBS_REQUIRE_LIVE = "1"` then
`python -m pytest tests/operations/test_phoneme_feature_sync_issue253.py -m "not requires_live_project" -q`
-- 9 passed / 2 deselected. Regression net: test_issue252_pos_feature_sync.py +
test_natural_class_feature_sync.py offline -- 34 passed / 0 failed. flake8 on both files: 0 issues
(pre-existing legacy F401s in PhonemeOperations' import block untouched; my test file is clean).

## Known limits / honestly-not-done

- The LIVE half of the mandatory write-path gate has NOT been executed. It needs the
  live token (rule 2), target_sandbox, and `FLEXLIBS_REQUIRE_LIVE=1`.
- The T9 `on_unresolved="raise"` flip is a BREAKING behavioural change: it needs its own
  commit + `CHANGELOG.md` entry (policy-flip commit, separate from the C2/C6/GUID work).
- Nothing has been committed in this corrective cycle.