# Live verification -- 4.13.1 release gate, full sweep, cycle 4 (fixes #828, #829)

**Project:** Target (sandbox + in-place), Sena 3 (sandbox/in-place) | **Date:** 2026-11-01
**run_mode:** live | **run_timestamp:** 2026-11-02T05:51:40Z (tests/live_status.json, read right after the main live run)
**Tree:** HEAD 667437ec plus uncommitted cycle-4 work (incl. regenerated tests/contract/snapshots/expected_contract.json).
**FieldWorks at start:** FieldWorks.exe NOT running. 9 python.exe processes were present (other sessions, e.g. flexicon-4c); no project lock was hit by any file.

## Commands
Offline: `python -m pytest -m "not requires_live_project" -q` -> **3964 passed, 0 failed**, 1296 deselected (baseline 3962).
File list: `git diff --name-only --diff-filter=AM v4.13.0..HEAD | grep -E '^tests/.*_live[.]py$'` (94 files) plus git-status live files (test_issue686 modified; test_issue828_pronunciation_media_live.py and test_issue829_lexreference_getall_live.py new) -> 96 unique files.
Live: `$env:FLEXLIBS_REQUIRE_LIVE="1"; python -m pytest <96 files> -m requires_live_project -q -rA`
Result: **4 failed, 118 passed, 0 skipped, 0 errors** in 121.59s (122 items; 1 deselected).

## Failures
- #684 test_issue684_move_media_file_after_hvo_refetch: KNOWN-GAP (expected).
- #740 test_issue740_remove_inflection_class_after_hvo_refetch: KNOWN-GAP (expected; IMoStemAllomorph.InflectionClassesRC).
- #752 test_add_dependent_clause_idempotent_via_resolved_hvo: KNOWN-GAP (expected; TypeError on DependentClausesRS).
- #825 test_override_in_effect_and_project_opens: NOT a code defect, env precondition. Test asserts `FLEXICON_FW_DIR must be set`; it was unset in the sweep shell (AssertionError at line 25). It is new to this range (commit 2bfca9c1), absent from cycle 2. Rerun once of that file alone with `FLEXICON_FW_DIR="C:\Program Files\SIL\FieldWorks 9"`: **1 passed** (4.55s), live_status.json run_mode live, run_timestamp 2026-11-02T05:52:07Z. Recommend the test skip/clearly document when the var is unset, or the release sweep always export it. Strictly this is an unexpected failure in the plain sweep; flagged for lead.

#686 now PASSES: both params [bare_icmmedia] and [icmfile] passed (no xfail, no skip). No skips at all (#724 no longer skips).

## Cycle-2 vs cycle-4 delta
Cycle 2: 4 failed / 97 passed / 1 skipped (102 items). Cycle 4: 4 failed / 118 passed / 0 skipped (122 items).
- Fixed: #686 (was KNOWN-GAP), #724 (skip gone, passes).
- Added passing: #828 (7 tests), #829 (3 tests), #686 now 2 params, plus other post-v4.13.0 live files.
- Still failing: #684, #740, #752 (known gaps). New: #825 env-precondition (passes with var set).

## Read-back (LCM re-queried inside tests; pytest -rA shows only prints, tests were not edited)
- #829: test prints `[INFO] GetAll=26 MembersOC walk=26` (Sena 3 sandbox): LexReference GetAll() count equals independent MembersOC walk. Other two #829 tests assert, after re-fetch by Hvo, that created hvo is in GetAll(s1), GetAll(s2), GetAll(e1), GetAll(e2) and that `{r.Hvo for r in GetAll()} == _walk_member_hvos(project)`.
- #686 (assertions, values not printed): after AddMediaFile on pron_src, media_hvo/file_hvo captured; after MoveMediaFile returned True, re-queried `[m.Hvo for m in pron.MediaFilesOS]` shows media_hvo absent from src (hvo via Object()), present in dst, and `moved_item.MediaFileRA.Hvo == file_hvo` (re-parented, not recreated).
- #828: 7 tests passed (AddMedia returns ICmMedia with label; RemoveMediaFile by icmmedia/hvo/icmfile; unrelated ICmFile raises; Pronunciation.Duplicate and LexEntry.Duplicate deep-copy media).
- Limitation: raw HVO integers for 686/828 are not printed by the tests, so they are not quoted here.

## Lock and restore notes
No lock failures; no in-place test failed mid-run; restore_target/restore_sena3 not run.

## Per-file result (all items passed unless shown; 825 row shows the plain-sweep result, rerun passed)
| File | Result |
|------|--------|
| test_issue640_getbeststring_live.py | PASS (1p) |
| test_issue642_etymology_duplicate_hvo_live.py | PASS (1p) |
| test_issue644_pronunciation_duplicate_hvo_live.py | PASS (1p) |
| test_issue646_allomorph_duplicate_hvo_live.py | PASS (1p) |
| test_issue648_pos_duplicate_hvo_live.py | PASS (2p) |
| test_issue650_datanotebook_duplicate_hvo_live.py | PASS (1p) |
| test_issue652_location_duplicate_hvo_live.py | PASS (1p) |
| test_issue654_person_duplicate_hvo_live.py | PASS (1p) |
| test_issue656_semanticdomain_duplicate_hvo_live.py | PASS (1p) |
| test_issue658_note_duplicate_hvo_live.py | PASS (1p) |
| test_issue660_anthropology_duplicate_hvo_live.py | PASS (1p) |
| test_issue662_possibilitylist_duplicate_hvo_live.py | PASS (2p) |
| test_issue664_check_duplicate_hvo_live.py | PASS (1p) |
| test_issue666_annotationdef_duplicate_hvo_live.py | PASS (1p) |
| test_issue668_possibility_item_duplicate_hvo_live.py | PASS (1p) |
| test_issue670_split_segment_hvo_live.py | PASS (1p) |
| test_issue672_publication_setisdefault_hvo_live.py | PASS (1p) |
| test_issue674_scrsection_moveto_hvo_live.py | PASS (1p) |
| test_issue676_check_delete_hvo_live.py | PASS (1p) |
| test_issue678_annotationdef_delete_hvo_live.py | PASS (1p) |
| test_issue680_note_delete_hvo_live.py | PASS (1p) |
| test_issue682_datanotebook_media_hvo_live.py | PASS (1p) |
| test_issue684_example_movemedia_hvo_live.py | FAIL (1f) |
| test_issue686_pronunciation_movemedia_hvo_live.py | PASS (2p) |
| test_issue688_lexsense_movepicture_hvo_live.py | PASS (1p) |
| test_issue690_lexsense_removepicture_hvo_live.py | PASS (1p) |
| test_issue692_lexsense_reorder_hvo_live.py | PASS (1p) |
| test_issue694_example_reorder_hvo_live.py | PASS (1p) |
| test_issue696_etymology_reorder_hvo_live.py | PASS (1p) |
| test_issue698_wfimorphbundle_reorder_hvo_live.py | PASS (1p) |
| test_issue700_pronunciation_reorder_hvo_live.py | PASS (1p) |
| test_issue702_dedup_hvo_verify_live.py | PASS (1p) |
| test_issue704_morphrule_reorder_hvo_live.py | PASS (1p) |
| test_issue706_naturalclass_segmentsrc_hvo_live.py | PASS (2p) |
| test_issue708_datanotebook_researcher_hvo_live.py | PASS (1p) |
| test_issue710_datanotebook_location_hvo_live.py | PASS (1p) |
| test_issue712_datanotebook_source_hvo_live.py | PASS (1p) |
| test_issue714_datanotebook_participant_hvo_live.py | PASS (1p) |
| test_issue716_reversal_sense_hvo_live.py | PASS (1p) |
| test_issue718_lexsense_semanticdomain_hvo_live.py | PASS (1p) |
| test_issue720_lexsense_usagetype_hvo_live.py | PASS (1p) |
| test_issue722_lexsense_domaintype_hvo_live.py | PASS (1p) |
| test_issue724_lexsense_anthrocode_hvo_live.py | PASS (1p) |
| test_issue726_lexsense_donotpublish_hvo_live.py | PASS (1p) |
| test_issue728_lexentry_donotpublish_hvo_live.py | PASS (1p) |
| test_issue730_lexentry_donotshowmainentry_hvo_live.py | PASS (1p) |
| test_issue732_example_donotpublish_hvo_live.py | PASS (1p) |
| test_issue734_semanticdomain_getsenses_hvo_live.py | PASS (1p) |
| test_issue736_overlay_possitems_hvo_live.py | PASS (2p) |
| test_issue738_variant_componentlexeme_hvo_live.py | PASS (2p) |
| test_issue740_allomorph_rc_hvo_live.py | FAIL (1f) |
| test_issue742_lexreference_target_hvo_live.py | PASS (1p) |
| test_issue744_lexreference_complex_entries_hvo_live.py | PASS (2p) |
| test_issue746_phoneme_removecode_hvo_live.py | PASS (2p) |
| test_issue748_phonrule_delete_hvo_live.py | PASS (1p) |
| test_issue750_possibility_item_delete_hvo_live.py | PASS (1p) |
| test_issue752_dependent_clause_hvo_live.py | FAIL (1f) |
| test_issue754_possibility_list_delete_hvo_live.py | PASS (1p) |
| test_issue756_location_delete_hvo_live.py | PASS (1p) |
| test_issue758_anthropology_delete_hvo_live.py | PASS (1p) |
| test_issue760_semanticdomain_delete_hvo_live.py | PASS (1p) |
| test_issue762_pos_delete_hvo_live.py | PASS (2p) |
| test_issue764_person_delete_hvo_live.py | PASS (1p) |
| test_issue766_lexref_deletetype_hvo_live.py | PASS (1p) |
| test_issue768_variant_delete_hvo_live.py | PASS (1p) |
| test_issue770_msa_exception_feature_hvo_live.py | PASS (2p) |
| test_issue772_overlay_delete_hvo_live.py | PASS (1p) |
| test_issue774_baseops_move_hvo_live.py | PASS (1p) |
| test_issue776_baseops_sort_hvo_live.py | PASS (2p) |
| test_issue778_msa_changeaffix_hvo_live.py | PASS (1p) |
| test_issue780_agent_delete_hvo_live.py | PASS (1p) |
| test_issue782_wfianalysis_delete_hvo_live.py | PASS (1p) |
| test_issue784_wfigloss_delete_hvo_live.py | PASS (1p) |
| test_issue786_wfimorphbundle_delete_hvo_live.py | PASS (1p) |
| test_issue788_paragraph_delete_hvo_live.py | PASS (1p) |
| test_issue790_segment_delete_hvo_live.py | PASS (1p) |
| test_issue792_discourse_delete_hvo_live.py | PASS (2p) |
| test_issue794_environment_delete_hvo_live.py | PASS (1p) |
| test_issue796_naturalclass_delete_hvo_live.py | PASS (1p) |
| test_issue798_phoneme_delete_hvo_live.py | PASS (1p) |
| test_issue800_stratum_delete_hvo_live.py | PASS (1p) |
| test_issue802_morphrule_delete_hvo_live.py | PASS (1p) |
| test_issue804_lexsense_delete_hvo_live.py | PASS (1p) |
| test_issue806_etymology_delete_hvo_live.py | PASS (1p) |
| test_issue808_pronunciation_delete_hvo_live.py | PASS (1p) |
| test_issue810_example_delete_hvo_live.py | PASS (1p) |
| test_issue812_allomorph_delete_hvo_live.py | PASS (1p) |
| test_issue814_lexref_delete_hvo_live.py | PASS (1p) |
| test_issue816_phonfeature_delete_hvo_live.py | PASS (2p) |
| test_issue818_datanotebook_delete_hvo_live.py | PASS (1p) |
| test_issue820_inflfeature_delete_hvo_live.py | PASS (1p) |
| test_issue824_wirerule_multi_context_live.py | PASS (1p) |
| test_issue825_fw_dir_override_live.py | FAIL (1f) |
| test_issue826_syncable_scalar_fields_live.py | PASS (5p) |
| test_issue828_pronunciation_media_live.py | PASS (7p) |
| test_issue829_lexreference_getall_live.py | PASS (3p) |
