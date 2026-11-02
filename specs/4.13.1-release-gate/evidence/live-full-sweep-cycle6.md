# Live verification -- 4.13.1 release gate, full sweep, cycle 6

**Project:** Target / Sena 3 (sandbox and in-place, per test fixtures) | **Date:** 2026-11-02
**run_mode:** live | **run_timestamp:** 2026-11-02T06:51:48Z (tests/live_status.json, read immediately after the live run)
**Tree:** HEAD 7668f58f plus uncommitted work (830/831/832 tests, modified 684/740/752 live files, source changes).
**Preconditions:** FieldWorks.exe not running (tasklist). 8 python.exe + 1 python3.exe from other sessions present; no lock hit.
Both FLEXLIBS_REQUIRE_LIVE=1 and FLEXICON_FW_DIR="C:\Program Files\SIL\FieldWorks 9" exported in the run shell.

## Commands
1. `python -m pytest -m "not requires_live_project" -q` -> **4006 passed, 0 failed**, 1301 deselected (104.75s).
2. File list: `git diff --name-only --diff-filter=AM v4.13.0..HEAD | grep -E '^tests/.*_live[.]py$'` plus `git status --short` live files (830/831/832 new; 684/740/752 modified), sort -u -> **99 unique files**.
   `--collect-only -m requires_live_project`: 127/128 collected (1 deselected) -> non-zero.
3. `python -m pytest <99 files> -m requires_live_project -q -rA -s`
   Result: **127 passed, 0 failed, 0 skipped, 0 errors**, 1 deselected, in 234.02s.
   (#825 test_override_in_effect_and_project_opens: PASSED, not skipped.)

## Failures
None. No lock/environment failures; no reruns needed.

## Delta vs cycle 4 (118 passed / 4 failed / 0 skipped of 122)
- Cycle 6: 127 passed / 0 failed / 0 skipped of 127 (+9 passed items, +5 items total, -4 failed).
- #684, #740, #752 known-gap failures now PASS (684: test_issue684_move_media_file_withdrawn_after_hvo_refetch; 740: remove_inflection_class_after_hvo_refetch and remove_phoneenv; 752: add_dependent_clause_idempotent_via_resolved_hvo).
- #825 now passes in the plain sweep (variable exported).
- New passing: #830 (3 tests), #831 (1), #832 (1).

## [EVIDENCE] read-back lines (verbatim from -s output)
```
[EVIDENCE-686] kind=bare_icmmedia readback media_hvo=10449 MediaFileRA.Hvo=10448 owner_pron_hvo=10446 src_pron_hvo=10445 dst_pron_hvo=10446 src_media_hvos=[] dst_media_hvos=[10449]
[EVIDENCE-686] kind=icmfile readback media_hvo=10449 MediaFileRA.Hvo=10448 owner_pron_hvo=10446 src_pron_hvo=10445 dst_pron_hvo=10446 src_media_hvos=[] dst_media_hvos=[10449]
[EVIDENCE-828] add readback media_hvo=10448 MediaFileRA.Hvo=10447 owner_pron_hvo=10445
[EVIDENCE-828] remove kind=icmmedia removed_media_hvo=10450 remaining_media_hvo=10448 remaining_MediaFileRA.Hvo=10447 owner_pron_hvo=10445
[EVIDENCE-828] remove kind=hvo removed_media_hvo=10450 remaining_media_hvo=10448 remaining_MediaFileRA.Hvo=10447 owner_pron_hvo=10445
[EVIDENCE-828] remove kind=icmfile removed_media_hvo=10450 remaining_media_hvo=10448 remaining_MediaFileRA.Hvo=10447 owner_pron_hvo=10445
[EVIDENCE-828] pron-dup readback src_media_hvo=10448 copy_media_hvo=10450 copy_MediaFileRA.Hvo=10447 copy_owner_pron_hvo=10449 dup_pron_hvo=10449
[EVIDENCE-828] entry-dup readback src_media_hvo=10448 copy_media_hvo=10453 copy_MediaFileRA.Hvo=10447 copy_owner_pron_hvo=10452
[EVIDENCE] affix allomorph hvo=58052 class hvo=152222 RC before=[]
[EVIDENCE] after add RC=[152222]
[EVIDENCE] after second add RC=[152222]
[EVIDENCE] after remove RC=[]
[EVIDENCE] stem allomorph hvo=42189 class hvo=152222
[EVIDENCE] MoAffixProcess present in sena3_sandbox: False
[EVIDENCE] example_hvo=10446 icmfile_before=1 audiovisual_before=None example_before={999000002: 'TEST_831_example'}
[EVIDENCE] example_hvo=10446 icmfile_after_add=1 audiovisual_after_add=None example_after_add={999000002: 'TEST_831_example'}
[EVIDENCE] example_hvo=10446 icmfile_final=1 audiovisual_final=None example_final={999000002: 'TEST_831_example'} get=[] count=0
[EVIDENCE] marker_hvo=10455 host_row=10449 r1=10450 r2=10451 r3=10452 r4_normal=10453
[EVIDENCE] pre-state RS=[]
[EVIDENCE] after add r1(obj), r2(hvo): RS=[10450, 10451]
[EVIDENCE] after re-add r1: RS=[10450, 10451]
[EVIDENCE] after insert r3@0: RS=[10452, 10450, 10451]
[EVIDENCE] after remove idx 0: RS=[10450, 10451]
[EVIDENCE] after add Normal r4: RS=[10450, 10451, 10453] warnings=1
[EVIDENCE] marker passed as element rejected; RS=[10450, 10451, 10453]
```
(#686 lines: media_hvo captured, moved from src_pron 10445 to dst_pron 10446, src_media_hvos=[] dst_media_hvos=[10449].
#830 lines: `[EVIDENCE]` lines with RC before/after add/second add/remove; #831 example hvo=10446 methods inert; #832 RS sequence lines.
#829 GetAll vs MembersOC-walk count line is not in the grep above if not tagged EVIDENCE; see -rA output.)

## Lock and restore notes
No lock failures; restore_target / restore_sena3 not run; sandboxes used where tests demanded; no leaked objects reported.

## Per-file result (tests passed per file; all PASS)
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
| test_issue684_example_movemedia_hvo_live.py | PASS (1p) |
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
| test_issue740_allomorph_rc_hvo_live.py | PASS (2p) |
| test_issue742_lexreference_target_hvo_live.py | PASS (1p) |
| test_issue744_lexreference_complex_entries_hvo_live.py | PASS (2p) |
| test_issue746_phoneme_removecode_hvo_live.py | PASS (2p) |
| test_issue748_phonrule_delete_hvo_live.py | PASS (1p) |
| test_issue750_possibility_item_delete_hvo_live.py | PASS (1p) |
| test_issue752_dependent_clause_hvo_live.py | PASS (1p) |
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
| test_issue825_fw_dir_override_live.py | PASS (1p) |
| test_issue826_syncable_scalar_fields_live.py | PASS (5p) |
| test_issue828_pronunciation_media_live.py | PASS (7p) |
| test_issue829_lexreference_getall_live.py | PASS (3p) |
| test_issue830_allomorph_inflection_class_live.py | PASS (3p) |
| test_issue831_example_media_live.py | PASS (1p) |
| test_issue832_dependent_clause_rows_live.py | PASS (1p) |

#829 read-back (verbatim): `[INFO] GetAll=26 MembersOC walk=26`
