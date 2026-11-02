# Live verification -- cycle5 #828/#829

**Project:** Sena 3 / Target via sandbox fixtures | **run_mode:** live | **Date:** 2026-11-02
FieldWorks not running (tasklist: 0 matches).

## Commands
- python -m pytest -m "not requires_live_project" -q  -> 3966 passed, 1296 deselected (baseline 3964; +2 = new test_issue828_pronunciation_media_offline.py::test_rejected_add_media_file_does_not_copy and ::test_remove_media_file_raises_when_no_media_collection)
- (4 live files) --collect-only -q -m requires_live_project -> 13 collected
- FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <686 live, 828 live, 829 live, 644 live> -m requires_live_project -q -s -> 13 passed, 0 failed, 0 skipped (no lock; no rerun needed)
- tests/live_status.json run_mode: live

## Read-back values
- 828 add: media_hvo=10448 MediaFileRA.Hvo=10447 owner_pron=10445
- 686 move: media_hvo=10449 MediaFileRA.Hvo=10448 src_media=[] dst_media=[10449]
- 828 remove (icmmedia/hvo/icmfile): removed 10450, remaining 10448 (MediaFileRA 10447)
- 828 pron-dup: copy_media 10450 -> MediaFileRA 10447 (same file as source); entry-dup copy_media 10453 -> 10447
- 829: GetAll=26, MembersOC walk=26

## Source diff
AddMediaFile: MediaFilesOS hasattr guard now precedes CopyToProject. RemoveMediaFile: raises FP_ParameterError("Pronunciation does not support media files") instead of returning.

## Result
[PASS]
