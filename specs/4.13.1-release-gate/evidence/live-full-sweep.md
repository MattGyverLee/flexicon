# Live verification -- 4.13.1 release gate, full sweep (v4.13.0..HEAD f2c41871)

**Project:** Target (sandbox copies via target_sandbox; 7 files in-place target_project, 1 sena3_project) | **Date:** 2026-11-01 (UTC 2026-11-02)
**run_mode:** live
**run_timestamp:** 2026-11-02T04:31:48Z (tests/live_status.json, read immediately after the run)
**FieldWorks running at start:** no (tasklist showed no FieldWorks/Flex process; Target not locked)

## Commands
File list: `git diff --name-only --diff-filter=AM v4.13.0..HEAD | grep -E '^tests/.*_live\.py$'` -> 90 files (matches expected 90).

Attempt 1 (aborted at collection, nothing executed):
`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <90 files> -m requires_live_project -q -rA`
-> "Interrupted: 1 error during collection": test_issue648_pos_duplicate_hvo_live.py has a module-level `from SIL.LCModel import IPartOfSpeech`, ModuleNotFoundError: No module named 'SIL' (FLEx is not yet initialised at collection time).

Attempt 2 (the evidence run; single invocation, all 90 files, one added flag so the collection error does not abort the rest):
`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <same 90 files> -m requires_live_project -q -rA --continue-on-collection-errors`
Result: **18 failed, 75 passed, 7 skipped, 1 error** in 182.56s (101 items). Deviation from the brief: `--continue-on-collection-errors` added.

## Per-file result (90 files)
By file: 67 PASS (some with partial skips), 17 FAIL, 1 ERROR (#648), 5 all-skipped.
SKIPPED means nothing was verified for that file.

| Issue | File | Result |
|-------|------|--------|
| #640 | test_issue640_getbeststring_live.py | FAIL |
| #642 | test_issue642_etymology_duplicate_hvo_live.py | PASS |
| #644 | test_issue644_pronunciation_duplicate_hvo_live.py | PASS |
| #646 | test_issue646_allomorph_duplicate_hvo_live.py | PASS |
| #648 | test_issue648_pos_duplicate_hvo_live.py | ERROR |
| #650 | test_issue650_datanotebook_duplicate_hvo_live.py | PASS |
| #652 | test_issue652_location_duplicate_hvo_live.py | PASS |
| #654 | test_issue654_person_duplicate_hvo_live.py | PASS |
| #656 | test_issue656_semanticdomain_duplicate_hvo_live.py | PASS |
| #658 | test_issue658_note_duplicate_hvo_live.py | FAIL |
| #660 | test_issue660_anthropology_duplicate_hvo_live.py | PASS |
| #662 | test_issue662_possibilitylist_duplicate_hvo_live.py | PASS |
| #664 | test_issue664_check_duplicate_hvo_live.py | FAIL |
| #666 | test_issue666_annotationdef_duplicate_hvo_live.py | PASS |
| #668 | test_issue668_possibility_item_duplicate_hvo_live.py | FAIL |
| #670 | test_issue670_split_segment_hvo_live.py | FAIL |
| #672 | test_issue672_publication_setisdefault_hvo_live.py | SKIPPED (all tests skipped, UNVERIFIED) |
| #674 | test_issue674_scrsection_moveto_hvo_live.py | PASS |
| #676 | test_issue676_check_delete_hvo_live.py | PASS |
| #678 | test_issue678_annotationdef_delete_hvo_live.py | PASS |
| #680 | test_issue680_note_delete_hvo_live.py | PASS |
| #682 | test_issue682_datanotebook_media_hvo_live.py | PASS |
| #684 | test_issue684_example_movemedia_hvo_live.py | FAIL |
| #686 | test_issue686_pronunciation_movemedia_hvo_live.py | FAIL |
| #688 | test_issue688_lexsense_movepicture_hvo_live.py | PASS |
| #690 | test_issue690_lexsense_removepicture_hvo_live.py | PASS |
| #692 | test_issue692_lexsense_reorder_hvo_live.py | FAIL |
| #694 | test_issue694_example_reorder_hvo_live.py | PASS |
| #696 | test_issue696_etymology_reorder_hvo_live.py | PASS |
| #698 | test_issue698_wfimorphbundle_reorder_hvo_live.py | PASS |
| #700 | test_issue700_pronunciation_reorder_hvo_live.py | PASS |
| #702 | test_issue702_dedup_hvo_verify_live.py | PASS |
| #704 | test_issue704_morphrule_reorder_hvo_live.py | PASS |
| #706 | test_issue706_naturalclass_segmentsrc_hvo_live.py | PASS |
| #708 | test_issue708_datanotebook_researcher_hvo_live.py | PASS |
| #710 | test_issue710_datanotebook_location_hvo_live.py | PASS |
| #712 | test_issue712_datanotebook_source_hvo_live.py | PASS |
| #714 | test_issue714_datanotebook_participant_hvo_live.py | PASS |
| #716 | test_issue716_reversal_sense_hvo_live.py | FAIL |
| #718 | test_issue718_lexsense_semanticdomain_hvo_live.py | PASS |
| #720 | test_issue720_lexsense_usagetype_hvo_live.py | SKIPPED (all tests skipped, UNVERIFIED) |
| #722 | test_issue722_lexsense_domaintype_hvo_live.py | SKIPPED (all tests skipped, UNVERIFIED) |
| #724 | test_issue724_lexsense_anthrocode_hvo_live.py | FAIL |
| #726 | test_issue726_lexsense_donotpublish_hvo_live.py | PASS |
| #728 | test_issue728_lexentry_donotpublish_hvo_live.py | PASS |
| #730 | test_issue730_lexentry_donotshowmainentry_hvo_live.py | PASS |
| #732 | test_issue732_example_donotpublish_hvo_live.py | PASS |
| #734 | test_issue734_semanticdomain_getsenses_hvo_live.py | PASS |
| #736 | test_issue736_overlay_possitems_hvo_live.py | PASS |
| #738 | test_issue738_variant_componentlexeme_hvo_live.py | SKIPPED (all tests skipped, UNVERIFIED) |
| #740 | test_issue740_allomorph_rc_hvo_live.py | SKIPPED (all tests skipped, UNVERIFIED) |
| #742 | test_issue742_lexreference_target_hvo_live.py | FAIL |
| #744 | test_issue744_lexreference_complex_entries_hvo_live.py | FAIL |
| #746 | test_issue746_phoneme_removecode_hvo_live.py | PASS |
| #748 | test_issue748_phonrule_delete_hvo_live.py | PASS |
| #750 | test_issue750_possibility_item_delete_hvo_live.py | PASS |
| #752 | test_issue752_dependent_clause_hvo_live.py | FAIL |
| #754 | test_issue754_possibility_list_delete_hvo_live.py | PASS |
| #756 | test_issue756_location_delete_hvo_live.py | PASS |
| #758 | test_issue758_anthropology_delete_hvo_live.py | PASS |
| #760 | test_issue760_semanticdomain_delete_hvo_live.py | PASS |
| #762 | test_issue762_pos_delete_hvo_live.py | PASS |
| #764 | test_issue764_person_delete_hvo_live.py | PASS |
| #766 | test_issue766_lexref_deletetype_hvo_live.py | PASS |
| #768 | test_issue768_variant_delete_hvo_live.py | PASS |
| #770 | test_issue770_msa_exception_feature_hvo_live.py | PASS |
| #772 | test_issue772_overlay_delete_hvo_live.py | PASS |
| #774 | test_issue774_baseops_move_hvo_live.py | FAIL |
| #778 | test_issue778_msa_changeaffix_hvo_live.py | PASS |
| #780 | test_issue780_agent_delete_hvo_live.py | PASS |
| #782 | test_issue782_wfianalysis_delete_hvo_live.py | FAIL |
| #784 | test_issue784_wfigloss_delete_hvo_live.py | PASS |
| #786 | test_issue786_wfimorphbundle_delete_hvo_live.py | PASS |
| #788 | test_issue788_paragraph_delete_hvo_live.py | PASS |
| #790 | test_issue790_segment_delete_hvo_live.py | PASS |
| #792 | test_issue792_discourse_delete_hvo_live.py | PASS |
| #794 | test_issue794_environment_delete_hvo_live.py | PASS |
| #796 | test_issue796_naturalclass_delete_hvo_live.py | PASS |
| #798 | test_issue798_phoneme_delete_hvo_live.py | PASS |
| #800 | test_issue800_stratum_delete_hvo_live.py | PASS |
| #802 | test_issue802_morphrule_delete_hvo_live.py | PASS |
| #804 | test_issue804_lexsense_delete_hvo_live.py | FAIL |
| #806 | test_issue806_etymology_delete_hvo_live.py | PASS |
| #808 | test_issue808_pronunciation_delete_hvo_live.py | PASS |
| #810 | test_issue810_example_delete_hvo_live.py | PASS |
| #812 | test_issue812_allomorph_delete_hvo_live.py | PASS |
| #814 | test_issue814_lexref_delete_hvo_live.py | FAIL |
| #816 | test_issue816_phonfeature_delete_hvo_live.py | PASS |
| #818 | test_issue818_datanotebook_delete_hvo_live.py | PASS |
| #820 | test_issue820_inflfeature_delete_hvo_live.py | PASS |

## Failure diagnoses (18 failed + 1 collection error)
Class: DEFECT = looks like a library defect; TEST = test bug / bad assumption; ENV = Target lacks data.
Diagnoses are quick reads of the traceback; "needs inspection" items were not run down.

| # | Test | Operations class.method | First error | Class |
|---|------|-------------------------|-------------|-------|
| 648 | test_issue648_pos_duplicate_hvo_live.py (collection) | POSOperations.Duplicate | ModuleNotFoundError: No module named 'SIL' (module-level import) | TEST (no test ran; #648 unverified) |
| 640 | TestIssue640GetBestStringLive::test_get_best_string_on_lex_sense_gloss | string-utils path used by LexSenseOperations.GetBestString | ImportError: cannot import name 'IMultiUnicode' from 'SIL.LCModel.Core.KernelInterfaces' | DEFECT (production import of a name absent in this LCM build; the #640 path fails live) |
| 658 | test_duplicate_reply_insert_after_raw_object_view | NoteOperations.Duplicate (reply) | AttributeError: 'ICmObject' object has no attribute 'Comment' | DEFECT (duplicate left as uncast ICmObject) |
| 664 | TestIssue664CheckDuplicateHvoLive::test_duplicate_insert_after_raw_object_view | CheckOperations.Duplicate | assert None is not None (test line 22) | TEST/ENV, needs inspection |
| 668 | test_publications_duplicate_insert_after_raw_object_view | PossibilityItemOperations.Duplicate | AttributeError: 'ICmObject' object has no attribute 'Name' | DEFECT (same uncast-duplicate pattern as 658) |
| 670 | test_split_inserts_after_raw_segment_in_segments_os | SegmentOperations.SplitSegment | assert 3 == (1 + 1) on SegmentsOS.Count | needs inspection (TEST baseline assumption or DEFECT) |
| 684 | test_issue684_move_media_file_after_hvo_refetch | LexExampleSentenceOperations.MoveMediaFile | AttributeError: 'ILexExampleSentence' object has no attribute 'MediaFilesOS' | TEST (setup) |
| 686 | test_issue686_move_media_file_after_hvo_refetch | PronunciationOperations.MoveMediaFile | TypeError: No method matches ICollection`1.Add: (ICmFile) | TEST (setup) |
| 692 | test_reorder_partial_list_with_raw_object_views | LexSenseOperations.Reorder | assert [10446, 10445, 10444, 10447] == [10446, 10445, 10447] | TEST likely (LexEntry.Create adds a default blank sense, hvo 10444) |
| 716 | test_issue716_remove_sense_after_hvo_refetch | ReversalEntryOperations.RemoveSense | IndexError at `project.LexEntry.GetAll()[0]` (Target has 0 lex entries) | ENV |
| 724 | test_issue724_remove_anthro_code_after_hvo_refetch | LexSenseOperations.RemoveAnthroCode | AttributeError: 'AnthropologyOperations' object has no attribute 'GetList' | TEST (non-existent API) |
| 742 | test_issue742_remove_target_after_hvo_refetch | LexReferenceOperations.RemoveTarget | Target needs at least 3 lex entries (0) | ENV |
| 744 | test_issue744_get_complex_form_entries_unique_hvos | LexReferenceOperations.GetComplexFormEntries | Target needs at least 3 lex entries (0) | ENV |
| 744 | test_issue744_get_component_entries_unique_hvos | LexReferenceOperations.GetComponentEntries | Target needs at least 3 lex entries (0) | ENV |
| 752 | test_add_dependent_clause_idempotent_via_resolved_hvo | AddDependentClause (library line: marker.DependentClausesRS.Add) | TypeError: No method matches ICollection`1.Add: (IConstChartClauseMarker) | DEFECT or TEST, needs inspection |
| 774 | test_move_down_finds_raw_sense_in_senses_os | BaseOperations.MoveDown (via LexSenseOperations) | AttributeError: 'FLExProject' object has no attribute 'LexiconEntries' | TEST (should be project.LexEntry) |
| 782 | test_issue782_delete_removes_from_analysesoc_by_hvo | WfiAnalysisOperations.Exists (Delete's own count assertion passed first) | FP_ParameterError: Object() could not resolve hvoOrGuid 10443 (KeyNotFoundException) | DEFECT in Exists (raises for a deleted hvo instead of returning False) |
| 804 | test_issue804_delete_removes_from_sensesos_by_hvo | LexSenseOperations.Delete | AttributeError: 'LexSenseOperations' object has no attribute 'Exists' (test line 38) | TEST (Delete itself not shown to fail) |
| 814 | test_issue814_delete_removes_from_membersoc_by_hvo | LexReferenceOperations.Delete | AttributeError: 'ILexSense' object has no attribute 'ReferringLexReferences' (test helper) | TEST |

## Skips (Target lacks data; fix unverified live)
672 (needs 2 publications), 720 (no usage types), 722 (no semantic domain items), 738 (no entries / variant types; 2 tests), 740 (no phonological environments / inflection classes; 2 tests).

## In-place tests and restore scripts
Eight files use target_project/sena3_project (676, 678, 680, 734, 748, 750, 818, 820). All their tests passed, no mid-test failure, so NEITHER restore script was run. `python scripts/restore_target.py --check` afterwards: Target present.

## Offline gate
`python -m pytest -m "not requires_live_project" -q` -> **3944 passed**, 1276 deselected (matches the previous 3944).

## Result
[FAIL] -- live run happened (run_mode live) but 18 tests failed, 1 collection error, 5 files fully skipped. #640, #658, #668 and #782 (Exists) look like genuine library defects.
