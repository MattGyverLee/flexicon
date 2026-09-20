# Verification Report -- lcm-member-truth-sweep, T4.7 (issue #259, checkpoint 4)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** specs/lcm-member-truth-sweep/evidence/live-T4-inflclass.md
**Project:** Sena 3 (sena3_sandbox -- tempdir copy of the .fwbackup;
real Sena 3 never opened)

## Scope-drift note (read this first)

The dispatch briefed item 5 as "pin SetInflectionClass still raises
AttributeError." While this verification was running, the campaign
progressed concurrently in the SAME working tree: a domain ruling (C11,
"warn") and its T4.5 implementation landed, unblocking
SetInflectionClass to write through the shared stem MSA and raise
FP_ParameterError (not AttributeError) for null/non-stem targets. The
concurrent process also edited the SAME test file
(tests/operations/test_lcm_member_truth_sweep.py) this task was
extending -- observed as the file's diff line count growing from 674 to
680 to 732 insertions across this single verification session, with
specs/lcm-member-truth-sweep/.crew-handoff.json and a new
reviews/cycle5-domain.md appearing mid-task. Item 5 below verifies the
CURRENT SetInflectionClass behaviour (which is what actually matters --
pinning stale behaviour the code has already moved past would not be
meaningful verification), not the brief's now-superseded expectation.
Full detail in the evidence file's "IMPORTANT: scope drift" section.
This is a process/coordination note for the lead, not a defect in T4.5's
implementation itself -- T4.5's actual behaviour verified clean.

## Claim vs. observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| Item 1: GetInflectionClass never raises across all 1932 bundles; None for null/non-stem MSA | 1932/1932 swept, 0 exceptions, null_msa=94 non_stem=1144 stem=694 non_none=0 (baseline, matches T4.4) | [PASS] |
| Item 2: GetSyncableProperties never raises; InflClassRA key absent iff no class | 1932/1932 swept, 0 exceptions, 0 mismatches vs independent raw-LCM computation -- required a monkeypatch to isolate from an unrelated pre-existing crash (see Blockers) | [PASS] (with caveat) |
| Item 3 (THE TRAP): planted a real class, read path returns it | Planted IMoInflClass hvo=152222 on stem MSA hvo=116694; re-read by HVO+cast confirms persistence; GetInflectionClass(bundle) re-read returns matching guid | [PASS] |
| Item 4: case-(a) deletion correct in all 3 Duplicate sites | WfiMorphBundleOperations.Duplicate, WfiAnalysisOperations.Duplicate(deep=True), WordformOperations.Duplicate(deep=True) all carry the planted class through the shared MSA, confirmed by re-read GUID match; all 3 sites covered, none skipped | [PASS] |
| Item 5: SetInflectionClass write path | INVERTED from brief (see scope-drift note): verified CURRENT "warn" behaviour -- positive path writes through and persists (re-read by HVO), null-MsaRA and non-stem-MSA both raise FP_ParameterError with no state change | [PASS] (against current code, not stale brief) |
| Item 6: regression | Campaign live file 23/23 passed; test_issue254_live_cycle2.py 8/8 passed; offline baseline 1878 passed/0 failed (matches programmer's reported figure exactly) | [PASS] |

## Mock suite (regression, supplementary)
Command: python -m pytest -m "not requires_live_project" -q
Result: 1878 passed, 809 deselected, 0 failed
Pre-existing failures (not caused by this change): none

## Blockers

None blocking this verdict, but two unrelated, pre-existing, live-confirmed
defects surfaced during this verification and should be filed as new
issues (full detail in the evidence file's "Additional live findings"):

1. GetSyncableProperties calls a nonexistent project.GetMultiStringDict()
   on the real FLExProject -- 1932/1932 bundles raise AttributeError,
   unconditionally, unrelated to InflClassRA. Same dead call reproduces
   in 7 other Operations classes (MediaOperations, DiscourseOperations,
   SegmentOperations x2, TextOperations x3, WfiGlossOperations,
   WordformOperations). Only masked because the mock suite stubs it via
   MagicMock auto-vivification. Worked around here with a scoped
   monkeypatch so item 2/3's InflClassRA claim could still be tested;
   the underlying defect is untouched and still broken.
2. project.Object(hvo) returns a bare ICmObject; calling
   GetInflectionClass(hvo) / SetInflectionClass(hvo, ...) with a raw
   HVO int (rather than an object) raises AttributeError on the
   MsaRA access inside __GetBundleObject's resolution path. Confirmed
   pre-existing (not from this cycle) by reproducing the identical
   failure on the untouched GetMSA(hvo). All doc examples already avoid
   this by passing objects, never ints -- the live test suite here does
   the same.

## Recommendation

APPROVE. All checkpoint-4 InflClassRA claims (T4.1/T4.2/T4.3/T4.5/T4.6)
are now live-verified with read-back-by-HVO evidence, including the
positive (planted-value) path that an observation-only sweep of stock
Sena 3 could not have proven. Recommend the lead: (a) note the
scope-drift/concurrent-edit hazard on this file for the crew's process,
(b) file two new issues for the out-of-scope defects above.
