# Live verification -- T6 (`MSAOperations.GetSyncableProperties`/`ApplySyncableProperties`)

**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup` -- the
real Target is never opened).
**New test file:** `tests/operations/test_issue251_msa_feature_sync.py`,
Section D (`TestMSASyncLiveRoundTrip`, 6 tests, all `requires_live_project`,
all `@pytest.mark.live_phase("MSAOperations", "modify")`). Sections A-C of
the same file (21 tests) are offline (static source locks + fake-object
dispatch coverage) and are not part of this live run.

## [PREDICTION] -- recorded BEFORE the live run

1. `test_stem_msa_capture_apply_roundtrip`: a real `MoStemMsa.MsFeaturesOA`
   populated via `_ApplyFeatureStruc` on a source stem, captured through
   `GetSyncableProperties(bare_object)`, applied onto a second, freshly
   created stem via `ApplySyncableProperties`, then RE-READ from a fresh
   `sandbox.Object(hvo)` fetch. Expect `props["MsFeaturesGuid"]` truthy and
   `props["MsFeatures"]["specs"]` equal to `{featGuid: valGuid}` on both the
   source capture and the target re-read.
2. `test_infl_aff_msa_capture_apply_roundtrip`: same shape for
   `MoInflAffMsa.InflFeatsOA`. Expect
   `reread_props["InflFeats"]["specs"] == {featGuid: valGuid}`.
3. `test_deriv_aff_msa_both_slots_roundtrip`: a `MoDerivAffMsa` with BOTH
   `FromMsFeaturesOA` and `ToMsFeaturesOA` populated with independent
   feature/value pairs. Expect capture to emit both `FromMsFeatures`/
   `ToMsFeatures` key-pairs correctly, and the re-read after apply onto a
   fresh target `MoDerivAffMsa` to match both slots independently (proves
   the `slot="From"`/`"To"` disambiguation actually reaches two distinct
   LCM properties, not one).
4. `test_unclassified_affix_msa_capture_and_apply_do_not_raise`: a REAL
   `MoUnclassifiedAffixMsa` (not a fake). Expect `GetSyncableProperties`
   returns `{}` and `ApplySyncableProperties(unclass, {})` does not raise
   (R2, against a genuine LCM object this time, not a Python fake).
5. `test_apply_raises_on_unresolved_feature_guid`: a bogus, never-minted
   feature GUID passed through the PUBLIC `ApplySyncableProperties`
   surface (not `_ApplyFeatureStruc` directly -- that path is already
   covered live by T4's `test_apply_feature_struc.py`). Expect
   `FP_ParameterError` raised, message containing the literal bogus GUID
   (C7, exercised through OUR dispatch, confirming propagation is not
   swallowed anywhere in `MSAOperations.ApplySyncableProperties`).
6. `test_hvo_and_guid_entry_paths_capture_feature_keys`: the SAME stem
   resolved via `GetSyncableProperties(hvo_int)` and
   `GetSyncableProperties(guid_str)` (never the already-typed object).
   Expect both entry paths to capture identical, non-empty
   `MsFeatures.specs` (C2 -- `FLExProject.Object(hvo_or_guid)` returns a
   bare `ICmObject`; `__GetMsaObject` must cast before any subtype access
   is attempted downstream).

Expected offline-suite baseline (measured immediately before this commit,
same shell, `python -m pytest tests/operations tests/contract -m "not
requires_live_project" -p no:cacheprovider -q`): **392 passed, 2 failed
(the known-foreign `TestPhase2JoinOrOpen` pair), 510 deselected** -- +21
passed / +6 deselected relative to the pre-T6 baseline of 371 passed / 504
deselected, matching exactly the 21 offline + 6 live tests this task adds,
with zero other-count change.

## [RESULT] -- recorded AFTER the live run

(to be filled in below this line once the live command has actually been
executed)
