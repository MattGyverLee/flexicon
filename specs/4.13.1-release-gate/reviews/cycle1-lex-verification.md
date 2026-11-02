# Verification Report -- 4.13.1 release gate (cycle 1)

**Verdict:** [FAIL]
**Live run:** yes | **run_mode:** live (run_timestamp 2026-11-02T04:31:48Z)
**Evidence:** specs/4.13.1-release-gate/evidence/live-full-sweep.md
**Project:** Target sandbox copies (+ in-place Target / Sena 3 for 8 files, all passed)

90 files run in one invocation with FLEXLIBS_REQUIRE_LIVE=1. `--continue-on-collection-errors` was added because #648's module-level `from SIL.LCModel import ...` aborted collection.
Results: 75 passed, 18 failed, 7 skipped, 1 collection error. Offline gate: 3944 passed. No restore scripts needed.

Suspected library defects: #640 (IMultiUnicode import fails in GetBestString), #658 and #668 (Duplicate leaves uncast ICmObject), #782 (WfiAnalysisOperations.Exists raises for a deleted hvo), possibly #752 and #670.
Likely test bugs: #648, 684, 686, 692, 724, 774, 804, 814, 664. Environment (Target has no lex entries): 716, 742, 744.
Unverified (all tests skipped for missing data): 672, 720, 722, 738, 740. #648 never collected.

Recommendation: FIX ISSUES. Do not tag until the defects are fixed and the failing and skipped files are re-run live.
