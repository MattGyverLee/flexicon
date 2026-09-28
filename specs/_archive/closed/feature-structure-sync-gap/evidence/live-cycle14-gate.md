# Live verification -- Cycle 14 Checkpoint 4 gate on T7 (#252)

**Project:** Target (write-path mutations, LEG 1/1a) + Sena 3 (read-path
enumeration, LEG 2/3) | **Fixture:** target_sandbox / sena3_sandbox in
disposable git worktree copies; nothing run against the in-place Target.
**Command pattern:** FLEXLIBS_REQUIRE_LIVE=1 python -m pytest FILE -m
requires_live_project -q (LEG 4/2), and single-file un-marked runs scoped
to test_issue252_pos_feature_sync.py only for the offline+live combined
check (LEG 1/1a).
**run_mode:** live (confirmed via tests/live_status.json after every
live invocation below)
**Date:** 2026-09-07

## Claim under test
T7 (POSOperations feature-struct sync, closes #252) lands safely: the
__ResolveObject cast is real (not dead code), the five characterizing
mutations kill the tests they claim to, P1's HVO-entry-path bug is real,
and the cast introduces zero regressions on the ~16 other call sites it
also affects.

## LEG 1 -- mutation re-run (fresh worktree wt-4b746a0 at 4b746a0)

Baseline hashes confirmed before any mutation:
flexicon/code/Grammar/POSOperations.py = f94b4d97efb54ac9f78a1a1c5b3a034303bac951
flexicon/code/BaseOperations.py = a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db

### M1 -- remove the ClassName == "PartOfSpeech" cast in __ResolveObject
Run: python -m pytest tests/operations/test_issue252_pos_feature_sync.py -q
(no -m filter, single file only -- to also catch the offline cast-shape
lock)
```
FAILED ...TestPOSSyncStatic::test_resolve_object_casts_on_classname_and_never_raises
FAILED ...TestPOSSyncLiveResolveObjectCast::test_hvo_path_casts_to_concrete_pos
FAILED ...TestPOSSyncLiveRoundTrip::test_hvo_entry_path_captures_name
3 failed, 23 passed, 50 warnings in 5.98s
```
SURVIVED (both feature-struct round trips + C7-raise + slot-ambiguity):
test_default_features_slot_capture_apply_roundtrip,
test_inher_feat_val_slot_capture_apply_roundtrip,
test_apply_raises_on_unresolved_feature_guid,
test_ambiguous_owner_without_slot_raises.
G1's central falsifier did NOT fire -- both feature-struct round trips
survived, confirming _ResolveFeatureStrucOwner IS a compensating cast
layer independent of __ResolveObject's own cast (re-validates cycle 10).
Restore verified: git hash-object = f94b4d97... (exact match).

### M2 -- presence gate -> truthiness (__ApplyFeatureStrucProp)
```
FAILED ...TestPOSSyncStatic::test_apply_gates_on_key_presence_not_truthiness
FAILED ...TestPOSSyncApplyPresenceGate::test_falsy_but_present_feature_struct_key_still_triggers_apply
FAILED ...TestPOSSyncApplyPresenceGate::test_falsy_but_present_guid_only_key_still_triggers_apply
3 failed, 23 passed, 50 warnings in 5.49s
```
SURVIVED: guid-only-truthy, neither-present (same T6b-known truthy-fixture
residual). Restore verified: f94b4d97...

### M3 -- on_unresolved="raise" -> "skip" in __ApplyFeatureStrucProp
Run: full-file -q (offline) then targeted live rerun with
FLEXLIBS_REQUIRE_LIVE=1 -m requires_live_project for the live test alone.
```
FAILED ...TestPOSSyncApplyRaisePropagationThroughPublicSurface::test_apply_propagates_fp_parameter_error_and_passes_raise_policy
FAILED ...TestPOSSyncLiveRoundTrip::test_apply_raises_on_unresolved_feature_guid
2 failed, 24 passed, 50 warnings in 5.28s
```
Live-only rerun (with FLEXLIBS_REQUIRE_LIVE=1) reconfirmed the single
live failure in isolation: "1 failed ... test_apply_raises_on_unresolved_feature_guid".
Restore verified: f94b4d97...

### M4 -- ambiguous-no-slot picks rows[0] (BaseOperations._ResolveFeatureStrucOwner)
First attempt at the mutation (removing the raise but leaving the
for/else unconditionally scoped) still raised via the for/else
fallthrough with an empty iterable -- corrected to gate the loop itself on
"slot is not None". Final mutation verified functionally correct (produces
rows[0] silently, no raise) before measuring kills.
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue252_pos_feature_sync.py -m requires_live_project -q
FAILED ...TestPOSSyncLiveSlotAmbiguityNoSlot::test_ambiguous_owner_without_slot_raises
1 failed, 5 passed, 20 deselected
```
Full-file rerun (offline+live combined): "1 failed, 25 passed" -- same
single kill, nothing else moved.
Restore verified: git hash-object flexicon/code/BaseOperations.py =
a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db (exact match).

### LEG 1a (G2a) -- T14a co-kill under M4, same worktree, same mutation live
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest "tests/operations/test_makefeatstruc_c3_live.py::TestMakeFeatStrucAmbiguousOwnerNoSlotLive::test_ambiguous_owner_without_slot_raises_through_makefeatstruc" -m requires_live_project -q
1 failed ... test_ambiguous_owner_without_slot_raises_through_makefeatstruc
```
G2a HELD -- the disclosed-but-unrun co-kill is REAL, run not reasoned.

### M5 -- InherFeatVal calls forced to slot="Default"
Both call sites mutated: GetSyncableProperties's
__CaptureFeatureStrucProp(props, pos, "InherFeatVal", "InherFeatVal") and
ApplySyncableProperties's
__ApplyFeatureStrucProp(pos, "InherFeatVal", "InherFeatVal", props)
-> slot arg forced to "Default" in both (key/props-name argument left
unchanged).
```
python -m pytest tests/operations/test_issue252_pos_feature_sync.py -q
FAILED ...TestPOSSyncCapture::test_capture_both_slots_populated
FAILED ...TestPOSSyncCapture::test_capture_only_one_slot_populated
FAILED ...TestPOSSyncApplyBothSlots::test_apply_dispatches_both_slots_with_correct_prop_names
FAILED ...TestPOSSyncLiveRoundTrip::test_inher_feat_val_slot_capture_apply_roundtrip
4 failed, 22 passed, 46 warnings in 5.35s
```
SURVIVED: test_default_features_slot_capture_apply_roundtrip (Default-only
round trip is invisible to the mis-routing, as predicted).
Restore verified: f94b4d97...

### Post-restore clean check (also serves as LEG 4)
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue252_pos_feature_sync.py -q
26 passed, 50 warnings in 5.31s
run_mode: live
```
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue252_pos_feature_sync.py -m requires_live_project -q
6 passed, 20 deselected, 50 warnings in 5.60s
run_mode: live
uncategorized_live_tests: []
```
Worktree git diff --stat empty after all five restores; git worktree
remove --force + git worktree prune -v silent.

## LEG 2 -- P2's live half (enumeration + both-sides run)

### 2(a) -- own enumeration (git grep at c26a017, verified byte-identical
to current HEAD 5efebb6 for every file below via
git diff --stat 1d88aa4 c26a017 -- tests/operations/ ..., which shows
ONLY POSOperations.py and the new test_issue252_...py changed)

Method: git grep for ".POS." / "POSOperations" / "project.POS" /
"IPartOfSpeech(" across tests/operations/*.py, then per-file AST pass
excluding doc-only mentions (test_natural_classes.py's single hit is
prose in a docstring, NOT code -- excluded), and transitively following
module-level helper functions (_first_pos, _locate_pos_hvo) and fixtures
that themselves reach project.POS/POSOperations, since a raw per-test-body
regex match alone under-counted files like test_set_pos_msa_dispatch.py
and test_msa_kind_and_change_variant.py whose tests call a helper rather
than touching .POS. inline.

Own enumeration: 16 files, 81 selected test node-ids (larger than the
12-file main-session floor list -- the floor list is a SUBSET of mine,
plus my own enumeration additionally finds test_abort_session_live.py,
test_apply_feature_struc.py, test_issue251_msa_feature_sync.py,
test_makefeatstruc_c3_live.py, test_segment_analysis_traversal.py, and
correctly EXCLUDES test_natural_classes.py's sole doc-only hit, which the
floor list's file-level grep could not distinguish). Per the dispatch's
own rule ("if larger, yours wins"), using mine.

Full 81-item node-id list actually passed to pytest (file::class::test):
```
tests/operations/test_abort_session_live.py::TestEnvelopeIsReopened::test_current_depth_is_one_again_after_abort
tests/operations/test_abort_session_live.py::TestSaveChangesIsUnusableInThisMode::test_save_changes_raises_commit_at_wrong_place
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucLegacyListLive::test_apply_legacy_list_creates_struct_preserves_guid_and_spec
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucLegacyListLive::test_apply_legacy_list_twice_is_idempotent
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucLegacyListLive::test_apply_raise_mode_raises_on_unresolved_feature_guid
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucLegacyListLive::test_apply_skip_mode_silently_skips_unresolved_guid
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucC4DictLive::test_apply_flat_c4_dict_creates_closed_value
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucC4DictLive::test_apply_nested_c4_dict_creates_complex_value_and_recurses
tests/operations/test_apply_feature_struc.py::TestApplyFeatureStrucC4DictLive::test_apply_c4_dict_raises_on_unresolved_type_guid
tests/operations/test_feature_struc_resolver.py::TestResolveFeatureStrucOwnerLive::test_resolves_concrete_owner_and_prop_name
tests/operations/test_feature_struc_resolver.py::TestResolveFeatureStrucOwnerLive::test_slot_ignored_on_single_row_owner_does_not_raise
tests/operations/test_feature_struc_resolver.py::TestResolveFeatureStrucOwnerLive::test_excluded_classname_raises_against_real_live_instance
tests/operations/test_feature_struc_resolver.py::TestGetFeatureStrucLive::test_nested_struct_round_trips_full_c4_shape
tests/operations/test_feature_struc_resolver.py::TestGetFeatureStrucLive::test_empty_but_present_struct_serializes_as_empty_specs_not_none
tests/operations/test_issue250_ws_case_divergence.py::TestWsCaseDivergenceLive::test_d4a_ws_map_case_divergent_resolves
tests/operations/test_issue250_ws_case_divergence.py::TestWsCaseDivergenceLive::test_d4b_no_ws_map_source_id_case_divergent_resolves
tests/operations/test_issue250_ws_case_divergence.py::TestWsCaseDivergenceLive::test_d4c_separator_divergent_resolves
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item1_2_msa_hasattr_base_vs_concrete_and_wrong_cast
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item3_pos_defaultfeatures_inherfeatval
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item5_6_nested_shape_and_counts_ngoreme
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item7_reproduce_256_makefeatstruc_on_msa_owner
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item9_ownership_first_rule
tests/operations/test_issue251_252_256_feature_struct_probe.py::test_item8b_createwithguid_roundtrips_guid_for_featstruc
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_stem_msa
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_infl_aff_msa
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_stem_msa_capture_apply_roundtrip
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_infl_aff_msa_capture_apply_roundtrip
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_deriv_aff_msa_both_slots_roundtrip
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_unclassified_affix_msa_capture_and_apply_do_not_raise
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_apply_raises_on_unresolved_feature_guid
tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveRoundTrip::test_hvo_and_guid_entry_paths_capture_feature_keys
tests/operations/test_lexsense_operations.py::TestLexSenseSetPartOfSpeechRegression::test_set_part_of_speech_on_new_sense
tests/operations/test_makefeatstruc_c3_live.py::TestMakeFeatStrucNestedDictLive::test_nested_dict_spec_round_trips_through_makefeatstruc
tests/operations/test_makefeatstruc_c3_live.py::TestMakeFeatStrucSlotDisambiguationLive::test_slot_disambiguates_from_and_to_through_makefeatstruc
tests/operations/test_makefeatstruc_c3_live.py::TestMakeFeatStrucAmbiguousOwnerNoSlotLive::test_ambiguous_owner_without_slot_raises_through_makefeatstruc
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_auto_on_stem_gives_stem_msa
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_auto_on_prefix_gives_infl_aff_msa
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_infl_on_prefix
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_deriv_on_prefix
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_deriv_with_explicit_from_and_to_pos
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_deriv_with_from_pos_only
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_unclassified_on_prefix
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_infl_short_circuits_when_already_infl
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_deriv_skips_short_circuit_when_infl_present
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_infl_on_stem_raises
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_deriv_on_stem_raises
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_msa_kind_unclassified_on_stem_raises
tests/operations/test_msa_kind_and_change_variant.py::TestSetPartOfSpeechMsaKind::test_invalid_msa_kind_raises
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_same_kind_returns_unchanged
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_infl_to_deriv
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_infl_to_unclassified
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_deriv_to_infl
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_deriv_to_unclassified
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_unclassified_to_infl
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_unclassified_to_deriv
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_infl_to_deriv_warning_lists_slots
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_infl_to_deriv_warning_lists_inflfeatsoa
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_old_msa_removed_when_no_senses_reference_it
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_repoints_all_senses_in_entry_referencing_old_msa
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_stem_msa_raises_parameter_error
tests/operations/test_msa_kind_and_change_variant.py::TestChangeAffixVariant::test_invalid_target_kind_raises
tests/operations/test_owner_cast_pattern.py::TestFeatureStructOwnerCastT1::test_cast_to_concrete_resolves_all_nine_owner_classnames
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_from_catalog_uses_canonical_guid
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_from_catalog_imports_localized_name
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_from_catalog_is_idempotent
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_from_catalog_accepts_bare_id
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_enhanced_with_gold_catalog_id
tests/operations/test_pos_catalog.py::TestPOSCatalog::test_create_unchanged_without_gold_prefix
tests/operations/test_pos_operations.py::TestPOSOperationsIntegration::test_getall_returns_pos
tests/operations/test_pos_operations.py::TestPOSOperationsIntegration::test_find_pos_by_name
tests/operations/test_segment_analysis_traversal.py::TestAnalysisOwnerResolvingHelpers::test_category_abbrev_resolves_owner_for_gloss_token
tests/operations/test_segment_analysis_traversal.py::TestAllFourTokenKindsGlossAndCategory::test_bare_analysis_token_has_no_gloss_but_may_have_category
tests/operations/test_segment_analysis_traversal.py::TestAllFourTokenKindsGlossAndCategory::test_gloss_token_gloss_and_category_match_owning_analysis
tests/operations/test_set_pos_msa_dispatch.py::TestSetPartOfSpeechMsaDispatch::test_stem_entry_gets_mo_stem_msa
tests/operations/test_set_pos_msa_dispatch.py::TestSetPartOfSpeechMsaDispatch::test_prefix_entry_gets_mo_infl_aff_msa
tests/operations/test_set_pos_msa_dispatch.py::TestSetPartOfSpeechMsaDispatch::test_suffix_entry_gets_mo_infl_aff_msa
tests/operations/test_set_pos_msa_dispatch.py::TestSetPartOfSpeechMsaDispatch::test_setpos_idempotent_on_affix
tests/operations/test_undoable_mode_live.py::TestCleanBlockCommits::test_committed_block_lands_on_the_undo_stack
tests/operations/test_undoable_mode_live.py::TestExceptionRollsBackLive::test_rolled_back_block_leaves_no_undo_entry
tests/operations/test_undoable_mode_live.py::TestPerOperationUnitOfWork::test_undo_label_is_the_per_site_label_not_the_method_name
tests/operations/test_undoable_mode_live.py::TestPerOperationUnitOfWork::test_a_failed_operation_adds_no_undo_entry
```

NOTE ON RISK PROFILE: test_set_pos_msa_dispatch.py,
test_msa_kind_and_change_variant.py, test_pos_catalog.py,
test_owner_cast_pattern.py, test_lexsense_operations.py,
test_segment_analysis_traversal.py open a REAL, NAMED, in-place project
directly ("Sena 3"/"Test"/"SampleLexicon"/"SampleLexicon3", first match
wins -- in practice "Sena 3") via their own pre-existing
writable_project/live_project fixtures, NOT a sandbox copy. This is
pre-existing test-suite design, unrelated to T7; each test that writes
cleans up its own TEST_/qZ_-prefixed entry in a finally: block. Ran
as-committed; see cleanup confirmation below.

### 2(b) -- both-sides run, same shell

AFTER (current HEAD 5efebb6, byte-identical to c26a017 for every file
in the set):
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <81 node-ids> -m requires_live_project -q
89 passed, 1 skipped, 721 warnings in 34.44s
collected 90 items (test_resolves_concrete_owner_and_prop_name auto-expands x10)
run_mode: live
```
Skip: test_issue250_ws_case_divergence.py::TestWsCaseDivergenceLive::test_d4c_separator_divergent_resolves
-- data-dependent LOUD SKIP ("ws.Id 'etu' has no '-' or '_' separator"),
unrelated to POS/T7, present at BOTH commits identically.

BEFORE (disposable worktree wt-1d88aa4 at 1d88aa4, pre-T7):
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <same 81 node-ids> -m requires_live_project -q
89 passed, 1 skipped, 721 warnings in 34.69s
run_mode: live
```
Same skip, same reason, same location.

Per-file dot-pattern (-v -q, so file-grouped dots) is BYTE-IDENTICAL
between the two runs -- diffed directly, zero differing lines.

### 2(c) -- delta
ZERO FLIPS in either direction. 89 passed / 1 skipped on both sides,
identical per-file pass/skip pattern. G3 and G3a HELD (G3a: no flip
occurred, so there is no direction to adjudicate -- the falsifier
condition for a P0 did not fire).

### 2(d) -- not needed (the enumerated set was non-empty; branch (b)/(c)
closed the leg, per the dispatch's own instruction to only fall back to
the tracked-probe route if the enumeration came back empty).

### Cleanup confirmation
Worktree wt-1d88aa4 removed via git worktree remove --force +
git worktree prune -v (silent). No writes were made against the
in-place, installed "Sena 3"/"Target" FieldWorks projects outside of the
pre-existing tests' own self-contained create/delete-in-finally
lifecycle (same as their routine use elsewhere in this suite); nothing was
left needing a restore_sena3.py/restore_target.py re-run as a result
of THIS leg specifically (the LEG 1/1a/3 mutation and probe work used
target_sandbox/sena3_sandbox tempdir copies exclusively and is
inherently non-destructive to the real installed projects).

## LEG 3 -- P1 re-derivation, tracked probe, both commits

Tracked (git-added + committed inside each disposable worktree, never
scratch-and-deleted) probe file
tests/operations/test_cycle14_leg3_p1_probe.py, calling
POSOperations.GetSyncableProperties(hvo) against the SAME pre-existing,
richly-populated Sena-3 POS (by Hvo) at both commits (fresh-POS-in-
Target was tried first and rejected as a probe design flaw -- a
freshly-created POS legitimately has no Description/CatalogSourceId text
regardless of the cast, so it under-reports at BOTH commits and cannot
discriminate; a real pre-existing populated POS is required):

At 1d88aa4 (pre-T7), worktree wt-1d88aa4-leg3b:
```
LEG3-P1-PROBE best_hvo=42183 keys=[]
LEG3-P1-PROBE present-of-four=[] count=0/4
1 passed in 4.80s   (run_mode: live)
```

At c26a017 (post-T7), worktree wt-c26a017-leg3:
```
LEG3-P1-PROBE best_hvo=42183 keys=['Abbreviation', 'CatalogSourceId', 'Description', 'Name']
LEG3-P1-PROBE present-of-four=['Abbreviation', 'CatalogSourceId', 'Description', 'Name'] count=4/4
1 passed in 4.42s   (run_mode: live)
```

Same hvo=42183 both times. G5 HELD exactly as predicted: literal {}
(0/4) at 1d88aa4, all 4 at c26a017. The deleted STEP 0 probe's
numbers are NOT cited -- this is an independent re-derivation.

## LEG 4 -- live file re-run as committed

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue252_pos_feature_sync.py -m requires_live_project -q
6 passed, 20 deselected, 50 warnings in 5.60s
run_mode: live
uncategorized_live_tests: []
```
G7 HELD exactly: 6 passed / 20 deselected, run_mode: live, no
telemetry-defect recurrence.

## LEG 5 -- comparator delta

AFTER (current tree, = c26a017 for every touched file):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception
2 failed, 416 passed, 518 deselected, 8 warnings in 3.66s
```

BEFORE (worktree wt-1d88aa4-leg5 at 1d88aa4), same shell session:
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception
2 failed, 396 passed, 512 deselected, 8 warnings in 5.57s
```

Delta: +20 passed (exactly T7's 20 offline tests), +6 deselected
(exactly T7's 6 live tests), failed unchanged at 2, SAME red set
(TestPhase2JoinOrOpen pair) on both sides. G6 HELD -- lands on the
NEW baseline (416/518, not a stale 396/392 misreading), delta measured in
this gate's own shell, not cited as a bare absolute.

## LEG 6 -- call-site enumeration

```
grep -n "self.__ResolveObject(" flexicon/code/Grammar/POSOperations.py
273, 401, 439, 474, 511, 555, 617, 673, 674, 711, 751, 792, 841, 913  (14 pre-existing)
1216, 1305  (2 new, inside the T7 sync methods)
```
Total: 16, not 15. G4 HELD -- the reported "15" in
reviews/cycle13-programmer.md section 5 and
.crew-handoff.json checkpoint_4.residual_named is off by one; the
correct denominator for the residual bound is 16 call sites (14
pre-existing + 2 new), matching the gate's own pre-committed line list
exactly.

## G9 -- Pyright diagnostics pre-existing

```
git show 4e9d152 -- flexicon/code/Grammar/POSOperations.py | grep "^@@"
@@ -1112,13 +1112,53 @@ ...
@@ -1126,11 +1166,28 @@ ...
@@ -1145,6 +1202,16 @@ ...
@@ -1172,20 +1239,166 @@ ...
```
All four hunks start at old-file line >=1112 -- the diff touches NOTHING
below ~1100. The super().ApplySyncableProperties(msa, base_props, ws_map,
fill_gaps=fill_gaps) call shape at MSAOperations.py:1000 is IDENTICAL
to POSOperations.py's own super().ApplySyncableProperties(pos,
base_props, ws_map, fill_gaps=fill_gaps) at :1314 -- same diagnostic
shape, already carried through a PASSED T6 gate. G9 HELD.

## G10 -- CompareTo side effect, CHANGELOG omission

```
git show 3eff177 -- CHANGELOG.md | grep -i "compareto\|struct.*guid"
(no output)
```
The 3eff177 CHANGELOG entry documents the capture/apply fix and the
HVO-entry-path bug fix in detail but contains zero mention of
CompareTo or the new "<key>Guid" struct-identity comparison side effect.
G10 HELD -- the omission is confirmed; this is recorded as a genuine
P2 (see report).

## G8 -- closing conditions 1-8, 10 independently re-derived

| # | Independent check performed by THIS gate | Result |
|---|---|---|
| 1 | grep FEATURE_STRUC_OWNER_TABLE in POSOperations.py -> 3 hits, all comments/docstrings, zero new table | MET |
| 2 | M4/M5 mutation results above (this leg) | MET |
| 3 | Read Section A of test_issue252_pos_feature_sync.py -- explicit allowlist + zero-hasattr AST tests present | MET |
| 4 | M1 kill of test_hvo_path_casts_to_concrete_pos with AttributeError (this leg) | MET |
| 5 | M2 kill of both falsy-but-present tests (this leg); truthy-fixture residual disclosed, unchanged | MET (residual disclosed) |
| 6 | Read TestPOSSyncApplyRaisePropagationThroughPublicSurface docstring (self-labels propagation-only) + M3 kill of the live enforcement test (this leg) | MET |
| 7 | git show 4e9d152 diff has zero new ws.Id/ws.Handle lines; test_issue250_defect4_ws_resolution.py = 21 passed (re-run this leg) | MET |
| 8 | LEG 4 re-run: 6 passed/20 deselected, run_mode live, uncategorized_live_tests=[] | MET |
| 10 | LEG 5 delta (this leg): +20/+6, failed unchanged at 2 | MET |

Condition 9 (this independent gate itself) is discharged by this report.

## Final tree-cleanliness confirmation

```
git worktree list        -> only the main worktree
git worktree prune -v    -> silent
git status --porcelain   -> only the five known pre-existing foreign items
git diff --stat          -> only .claude/ralph-loop.local.md (pre-existing, not ours)
```

## Result
PASS -- every G1-G10 prediction touched by this gate's scope is
adjudicated in reviews/cycle14-verification.md; Checkpoint 4's
condition 9 is now MET. Two genuine findings recorded: a P2 (CompareTo
CHANGELOG omission) and a bookkeeping correction (16 vs 15 call sites,
non-blocking).
