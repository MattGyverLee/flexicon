# Cycle 4 verification (lex-verification)

**Verdict: PASS on #828/#829/#686 expectations; one unexpected failure (#825, env precondition) flagged.**
run_mode: live (ts 2026-11-02T05:51:40Z). Offline: 3964 passed, 0 failed.
Live (96 files, REQUIRE_LIVE=1): 4 failed / 118 passed / 0 skipped (cycle 2: 4/97/1).

- #686 passes (both params, no xfail/skip). #828 7/7 pass. #829 3/3 pass (GetAll=26 == MembersOC walk=26).
- Known gaps still failing as expected: #684, #740, #752.
- Not-in-list failure: test_issue825_fw_dir_override_live fails when FLEXICON_FW_DIR is unset (test asserts the var is set); rerun with var set to FieldWorks 9 dir passes. Not a library regression; test should skip when unset or sweep must export it.
- No locks, FieldWorks not running, no restores needed. Other python procs present.
- Read-back: 686/828 HVO values are asserted but not printed; only the 829 count is quoted.
Evidence: specs/4.13.1-release-gate/evidence/live-full-sweep-cycle4.md; diff: reviews/cycle4-diff.patch (891 lines, 12 files).
