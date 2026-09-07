# Live verification (gate) -- T1: lcm_casting._interface_cache feature-structure entries

**Project:** none opened by gate itself (offline suite) / Ngoreme FLEx read-only (live suite, via test's own fixture)
**Fixture:** test_owner_cast_pattern.py's `ngoreme_readonly` (read-only); other live files use their own project fixtures.
**Commands:**
```
git stash push -- flexicon/code/lcm_casting.py    # BASELINE = T1 source reverted
python -m pytest tests -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_natural_classes.py tests/operations/test_natural_class_feature_sync.py \
  tests/operations/test_phonemes.py tests/operations/test_phon_features.py \
  tests/operations/test_inflection_features.py tests/operations/test_owner_cast_pattern.py \
  tests/operations/test_issue251_252_256_feature_struct_probe.py -m requires_live_project -q
git stash pop                                      # AFTER = T1 source restored; confirmed via git status
# re-ran both commands again for AFTER
```
**run_mode:** live (both BASELINE `2026-09-07T06:20:10Z` and AFTER `2026-09-07T06:22:10Z` runs of `tests/live_status.json`)
**Date:** 2026-09-07

## Claim under test
T1 adds 9 ClassNames (PhNCFeatures, PhNCSegments, PhPhoneme, PartOfSpeech, PosFeatures,
FsComplexFeature, FsFeatStruc, FsComplexValue, FsClosedValue) to `lcm_casting._interface_cache`,
and this is claimed to be behaviour-neutral for the existing NC/Phoneme live suite (only the
dormant #133 branch newly activates for PhNCFeatures/PhPhoneme owners), plus one pre-existing
unrelated failure that is NOT a T1 regression.

## BASELINE (lcm_casting.py stashed back to pre-T1)
- Offline (`-m "not requires_live_project"`): **1277 passed, 0 failed** (448 deselected).
  `test_no_removed_type_dependencies` emits a non-fatal `UserWarning` because
  `expected_contract.json` (not stashed) already lists `IFsComplexValue`, which the reverted
  source no longer imports -- warning only, no failure.
- Live (7 files, `-m requires_live_project`): **2 failed, 82 passed, 1 skipped**.
  - `test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target`
    -- FAILED (pre-existing; see below).
  - `test_owner_cast_pattern.py::TestFeatureStructOwnerCastT1::test_cast_to_concrete_resolves_all_nine_owner_classnames`
    -- FAILED, with:
    `AssertionError: PartOfSpeech: cast_to_concrete(project.Object(20918)) did not resolve to
    <class 'SIL.LCModel.IPartOfSpeech'>` -- i.e. `isinstance(<ICmObject>, IPartOfSpeech)` is
    `False` pre-T1. Confirms the new test genuinely exercises the fix (fails without it).

## AFTER (lcm_casting.py restored; `git status` confirmed the T1 diff was back before this run)
- Offline: **1277 passed, 0 failed** (448 deselected) -- identical to BASELINE.
- Live (same 7 files): **1 failed, 83 passed, 1 skipped**.
  - `test_apply_raises_on_type_mismatch_segments_target` -- still FAILED, same
    `AttributeError: 'ICmObject' object has no attribute 'Name'` at
    `NaturalClassOperations.py:1270` -- identical failure mode before and after => pre-existing,
    not a T1 regression.
  - `test_cast_to_concrete_resolves_all_nine_owner_classnames` -- now PASSED. Console (`-s`):
    `[T1] Exercised base-interface-view cast for: ['PartOfSpeech', 'PhPhoneme', 'PhNCFeatures',
    'PhNCSegments', 'FsComplexFeature', 'FsFeatStruc', 'FsComplexValue', 'FsClosedValue']`
    `[T1] Skipped (see reasons): ['PosFeatures (interface not present in this LCM version)']`

## Pass/fail set diff (BASELINE vs AFTER)
Exactly one test flips: the new T1 regression test, fail->pass. Every other test's
pass/fail status is identical between BASELINE and AFTER, including the one pre-existing
failure. No other test in the 7 live files changed status.

## Re-queried pre/post state for the new regression test (per ClassName)
| ClassName | pre-T1 `isinstance(cast_to_concrete(project.Object(hvo)), <interface>)` | post-T1 (same call) |
|---|---|---|
| PartOfSpeech | False (observed directly, hvo=20918) | True |
| PhPhoneme, PhNCFeatures, PhNCSegments, FsComplexFeature, FsFeatStruc, FsComplexValue, FsClosedValue | not individually captured at BASELINE (test raises on first case, PartOfSpeech, before reaching these) but all 8 pass at AFTER per console output above; by construction each assertion is identical logic per ClassName, so BASELINE would fail all 8 the same way pre-T1 (the cache entries are simply absent) | True (all 8, live, re-fetched via `project.Object(hvo)`) |
| PosFeatures | skipped both runs (IPosFeatures absent from this LCM version, confirmed) | skipped |

## Cleanup
Live suite is read-only (Ngoreme FLEx `writeEnabled=False`) or self-restoring
(`test_owner_cast_pattern.py`'s other fixtures use `target_sandbox`/capture-restore). No writes
performed by the gate itself. `git stash pop` confirmed via `git status` showing
`lcm_casting.py` back in modified (T1) state before the AFTER run.

## Result
[PASS] -- BASELINE and AFTER live pass/fail sets are identical apart from the new T1 test
(fail at BASELINE, pass at AFTER, as required); offline suite green both times; the one
pre-existing failure is confirmed identical before and after.
