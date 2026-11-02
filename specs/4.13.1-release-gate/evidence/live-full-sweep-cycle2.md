# Live verification -- 4.13.1 release gate, full sweep, cycle 2

**Project:** Target (sandbox + in-place), Sena 3 in-place for one file | **Date:** 2026-11-01
**run_mode:** live | **run_timestamp:** 2026-11-02T04:55:54Z (tests/live_status.json, read right after the live run)
**FieldWorks running at start:** no (tasklist clean)
**Untracked new files:** none outside specs/ (specs/4.13.1-release-gate/evidence/live-full-sweep.md, specs/4.13.1-release-gate/reviews/). No new *_live.py files.

## Commands
File list: `git diff --name-only --diff-filter=AM v4.13.0..HEAD | grep -E '^tests/.*_live[.]py$'` -> 90 files.
`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <90 files> -m requires_live_project -q -rA` (no --continue-on-collection-errors; collected cleanly)
Result: **4 failed, 97 passed, 1 skipped, 0 errors** in 181.30s (102 items).
Offline: `python -m pytest -m "not requires_live_project" -q` -> **3946 passed**, 1276 deselected.
No in-place test failed mid-run, so no restore_target/restore_sena3 was needed.
Diff for QC: specs/4.13.1-release-gate/reviews/cycle2-diff.patch (git diff f2c41871, 949 lines).

## Failures (all KNOWN-GAP)
- #684 test_issue684_move_media_file_after_hvo_refetch: KNOWN-GAP, ILexExampleSentence has no MediaFilesOS.
- #686 test_issue686_move_media_file_after_hvo_refetch: KNOWN-GAP, ICollection.Add(ICmFile) rejected by ICmMedia collection.
- #740 test_issue740_remove_inflection_class_after_hvo_refetch: KNOWN-GAP, IMoStemAllomorph has no InflectionClassesRC.
- #752 test_add_dependent_clause_idempotent_via_resolved_hvo: KNOWN-GAP, DependentClausesRS Add rejects IConstChartClauseMarker.

## Skips
- #724 (1 test): KNOWN, Target has no anthropology codes (still skipping; unverified).

## Cycle-1 vs cycle-2 delta
Cycle 1: 18 failed, 75 passed, 7 skipped, 1 error (101 items, needed --continue-on-collection-errors).
Cycle 2: 4 failed, 97 passed, 1 skipped, 0 error. Collection error (#648) fixed; non-gap failures fixed; 6 fewer skips; new #752 test fails as known gap.

## Per-file result (p/f/s = passed/failed/skipped tests)
| File | Result |
|------|--------|
| test_issue640_getbeststring_live.py | PASS (1p/0f/0s) |
| test_issue642_etymology_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue644_pronunciation_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue646_allomorph_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue648_pos_duplicate_hvo_live.py | PASS (2p/0f/0s) |
| test_issue650_datanotebook_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue652_location_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue654_person_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue656_semanticdomain_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue658_note_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue660_anthropology_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue662_possibilitylist_duplicate_hvo_live.py | PASS (2p/0f/0s) |
| test_issue664_check_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue666_annotationdef_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue668_possibility_item_duplicate_hvo_live.py | PASS (1p/0f/0s) |
| test_issue670_split_segment_hvo_live.py | PASS (1p/0f/0s) |
| test_issue672_publication_setisdefault_hvo_live.py | PASS (1p/0f/0s) |
| test_issue674_scrsection_moveto_hvo_live.py | PASS (1p/0f/0s) |
| test_issue676_check_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue678_annotationdef_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue680_note_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue682_datanotebook_media_hvo_live.py | PASS (1p/0f/0s) |
| test_issue684_example_movemedia_hvo_live.py | FAIL (0p/1f/0s) |
| test_issue686_pronunciation_movemedia_hvo_live.py | FAIL (0p/1f/0s) |
| test_issue688_lexsense_movepicture_hvo_live.py | PASS (1p/0f/0s) |
| test_issue690_lexsense_removepicture_hvo_live.py | PASS (1p/0f/0s) |
| test_issue692_lexsense_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue694_example_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue696_etymology_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue698_wfimorphbundle_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue700_pronunciation_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue702_dedup_hvo_verify_live.py | PASS (1p/0f/0s) |
| test_issue704_morphrule_reorder_hvo_live.py | PASS (1p/0f/0s) |
| test_issue706_naturalclass_segmentsrc_hvo_live.py | PASS (2p/0f/0s) |
| test_issue708_datanotebook_researcher_hvo_live.py | PASS (1p/0f/0s) |
| test_issue710_datanotebook_location_hvo_live.py | PASS (1p/0f/0s) |
| test_issue712_datanotebook_source_hvo_live.py | PASS (1p/0f/0s) |
| test_issue714_datanotebook_participant_hvo_live.py | PASS (1p/0f/0s) |
| test_issue716_reversal_sense_hvo_live.py | PASS (1p/0f/0s) |
| test_issue718_lexsense_semanticdomain_hvo_live.py | PASS (1p/0f/0s) |
| test_issue720_lexsense_usagetype_hvo_live.py | PASS (1p/0f/0s) |
| test_issue722_lexsense_domaintype_hvo_live.py | PASS (1p/0f/0s) |
| test_issue724_lexsense_anthrocode_hvo_live.py | SKIPPED (0p/0f/1s) |
| test_issue726_lexsense_donotpublish_hvo_live.py | PASS (1p/0f/0s) |
| test_issue728_lexentry_donotpublish_hvo_live.py | PASS (1p/0f/0s) |
| test_issue730_lexentry_donotshowmainentry_hvo_live.py | PASS (1p/0f/0s) |
| test_issue732_example_donotpublish_hvo_live.py | PASS (1p/0f/0s) |
| test_issue734_semanticdomain_getsenses_hvo_live.py | PASS (1p/0f/0s) |
| test_issue736_overlay_possitems_hvo_live.py | PASS (2p/0f/0s) |
| test_issue738_variant_componentlexeme_hvo_live.py | PASS (2p/0f/0s) |
| test_issue740_allomorph_rc_hvo_live.py | FAIL (1p/1f/0s) |
| test_issue742_lexreference_target_hvo_live.py | PASS (1p/0f/0s) |
| test_issue744_lexreference_complex_entries_hvo_live.py | PASS (2p/0f/0s) |
| test_issue746_phoneme_removecode_hvo_live.py | PASS (2p/0f/0s) |
| test_issue748_phonrule_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue750_possibility_item_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue752_dependent_clause_hvo_live.py | FAIL (0p/1f/0s) |
| test_issue754_possibility_list_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue756_location_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue758_anthropology_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue760_semanticdomain_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue762_pos_delete_hvo_live.py | PASS (2p/0f/0s) |
| test_issue764_person_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue766_lexref_deletetype_hvo_live.py | PASS (1p/0f/0s) |
| test_issue768_variant_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue770_msa_exception_feature_hvo_live.py | PASS (2p/0f/0s) |
| test_issue772_overlay_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue774_baseops_move_hvo_live.py | PASS (1p/0f/0s) |
| test_issue778_msa_changeaffix_hvo_live.py | PASS (1p/0f/0s) |
| test_issue780_agent_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue782_wfianalysis_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue784_wfigloss_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue786_wfimorphbundle_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue788_paragraph_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue790_segment_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue792_discourse_delete_hvo_live.py | PASS (2p/0f/0s) |
| test_issue794_environment_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue796_naturalclass_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue798_phoneme_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue800_stratum_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue802_morphrule_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue804_lexsense_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue806_etymology_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue808_pronunciation_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue810_example_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue812_allomorph_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue814_lexref_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue816_phonfeature_delete_hvo_live.py | PASS (2p/0f/0s) |
| test_issue818_datanotebook_delete_hvo_live.py | PASS (1p/0f/0s) |
| test_issue820_inflfeature_delete_hvo_live.py | PASS (1p/0f/0s) |
