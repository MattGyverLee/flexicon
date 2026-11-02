# Cycle 5 verification -- #828/#829

Verdict: PASS (live)

- Offline: 3966 passed, 0 failed (baseline 3964; +2 new offline tests in test_issue828_pronunciation_media_offline.py: test_rejected_add_media_file_does_not_copy, test_remove_media_file_raises_when_no_media_collection).
- Live: 13 collected, 13 passed, 0 failed, 0 skipped (FLEXLIBS_REQUIRE_LIVE=1); live_status.json run_mode = live; FieldWorks not running; no lock failures.
- Read-back: 828 add media Hvo 10448 -> MediaFileRA Hvo 10447; 686 move media 10449 -> MediaFileRA 10448 (moved to dst, src empty).
- 829: GetAll=26 == MembersOC walk=26.
- Diff confirmed: AddMediaFile capability check precedes CopyToProject; RemoveMediaFile raises FP_ParameterError.

Evidence: specs/4.13.1-release-gate/evidence/live-cycle5-828-829.md
