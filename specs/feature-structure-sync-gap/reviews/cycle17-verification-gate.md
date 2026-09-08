# Cycle-17 Checkpoint 5 -- INDEPENDENT verification gate report

Verifier did NOT implement T8. Every mutation/measurement here was re-run
from scratch in disposable worktrees (`git worktree add HEAD`), independent
of the implementer's numbers. Full detail:
specs/feature-structure-sync-gap/evidence/live-cycle17-gate.md.

## Per-leg verdicts

- LEG 4a (baseline): [PASS]. Two runs of `pytest tests/operations
  tests/contract -m "not requires_live_project" -q` both gave `2 failed,
  437 passed, 524 deselected`; red set exactly
  `TestPhase2JoinOrOpen::{test_rollback_flag_set_true_on_exception,
  test_depth_restored_on_exception}`. No third failure.
- LEG 1 (HVO axis, G1): [PASS]. New live file
  test_t8_hvo_path_gate.py passes a genuine `int` (not an already-typed
  object) through GetForm and SetForm. Live at HEAD: 2 passed, `run_mode:
  live` confirmed. Under M-G1 (delete the two ClassName cast branches,
  __GetAllomorphObject:1364-1369) in a disposable worktree: both RED --
  `AttributeError: 'ICmObject' object has no attribute 'Form'` at :854 and
  :906. Worktree hash-verified restored and removed.
- LEG 2 (hasattr gates, G2/G2b): [PASS]. Live disposable probe (never
  committed) passed a free ILexEntry.Hvo into GetSyncableProperties: no
  raise, dict exactly `{'Form': {}, 'MorphTypeRA': None}`. New committed
  offline test test_t8_allomorph_hasattr_allowlist.py scans the WHOLE
  module by first-argument identity (`allomorph`), asserts exactly 3 such
  calls (Form/IsAbstract/MorphTypeRA, all in GetSyncableProperties) and
  separately documents 7 total hasattr calls in the file. Proven
  non-tautological: inserting a 4th `hasattr(allomorph,
  "MsEnvFeaturesOA")` inside GetForm in a worktree turned the new test RED
  (2 failed) while the SHIPPED per-function test stayed fully green (21
  passed) under the identical mutation -- exactly the gap the archivist
  flagged. Worktree hash-verified restored and removed. Per the lead's
  binding ruling, the silent-drop shape is recorded in the evidence file
  only, never pinned as expected behaviour by a durable test.
- LEG 3 (independent reproduction, G3): [SPLIT]. Fresh worktree, baseline 6
  live tests pass. M-T8-1 (remove the cast): 2 failed, 4 passed. Actual
  dead set = {TestT8LiveDirectCast::test_hvo_path_casts_to_concrete_affix_allomorph,
  TestT8LiveRoundTrip::test_hvo_entry_path_captures_form}. The prediction
  named the dead set as {TestT8LiveDirectCast, TestT8LiveHasattrTrap} --
  but TestT8LiveHasattrTrap's one test reads sandbox.Object(hvo) directly
  and never calls __GetAllomorphObject, so it structurally cannot die under
  this mutation and correctly survived. The substantive claim (asymmetric
  split: direct-cast dies, HVO-entry Form-capture dies, round-trip
  survives) is fully confirmed -- just against
  TestT8LiveRoundTrip::test_hvo_entry_path_captures_form, not the class
  literally named. Labeling error in the prediction text, not a code
  defect or an un-killed mutation; nothing predicted-to-survive died.
  M-T8-2 (delete the :594 ClassName guard): 1 failed exactly as predicted,
  `FP_ParameterError: ...ClassName 'MoStemAllomorph' is not a recognized
  feature-structure owner...`. Disclosed collateral: M-T8-1 also kills the
  offline test_get_allomorph_object_casts_on_classname_and_never_raises
  source-pattern test (an extra, correct kill, not a miss). All hashes
  restored and verified; worktree removed.
- LEG 4b (post-gate delta): [PASS]. Both runs: `2 failed, 439 passed, 526
  deselected`. `passed` +2 = the 2 new offline allowlist tests;
  `deselected` +2 = the 2 new live HVO-gate tests (deselected under
  `-m "not requires_live_project"`). `failed` unchanged. Fully explained.

## Prediction adjudication

- G1: HELD -- live-red under M-G1 on a genuine int through GetForm and
  SetForm; deciding observation is the two AttributeError failures above.
- G2: HELD exactly -- disposable probe returned `{'Form': {}, 'MorphTypeRA':
  None}`, no raise, on a real ILexEntry passed by HVO.
- G2b: HELD -- 7 total hasattr calls, 3 scoped to `allomorph` (all in
  GetSyncableProperties, all in {Form, IsAbstract, MorphTypeRA}), matching
  the archivist's static table and reproduced live by the new test.
- G3: SPLIT -- M-T8-2 half HELD exactly. M-T8-1's SUBSTANTIVE claim
  (asymmetric split, round-trip survives) HELD, but the LITERAL falsifier
  wording ("TestT8LiveHasattrTrap dies") is FALSIFIED -- that test cannot
  die under this mutation since it never calls the mutated method.
- G4: HELD exactly -- identical 2/437/524 baseline reproduced twice, then
  2/439/526 after this gate's own 2 offline + 2 live additions.
- G5: not re-adjudicated (already DONE by the cycle-17 archivist,
  PASS-WITH-QUALIFIER; out of scope for this gate).

## Named falsifiers for zero-change claims

- "No third failure / failed stays 2" (LEG 4a/4b): falsifier is any third
  distinct failing node ID across 4 total offline runs -- none observed.
- "No predicted-survivor died" under M-T8-1: falsifier is any of
  TestT8LiveRoundTrip::{test_ms_env_features_capture_apply_roundtrip,
  test_apply_raises_on_unresolved_feature_guid} or
  TestT8LiveStemAllomorphNoFeatureKeys failing -- all traverse
  __GetAllomorphObject indirectly via already-typed objects and all three
  stayed green.
- M-T8-2 "no other test affected": falsifier is any of the other 5 shipped
  live tests failing -- none did (1 failed, 5 passed).

## Blockers
None. Target sandbox reachable in every worktree; no lock encountered.

## P0/P1/P2
- P0: none. Every mutation applied (M-G1, the GetForm hasattr insertion,
  M-T8-1, M-T8-2) was caught by at least one test, live or offline.
- P1: the cycle-17 prediction file's G3 falsifier names
  `TestT8LiveHasattrTrap` as one of the two tests that dies under M-T8-1;
  the test that actually dies for the "HVO-entry" claim is
  `TestT8LiveRoundTrip::test_hvo_entry_path_captures_form`. Correct the
  prediction document so a future cycle does not misread
  TestT8LiveHasattrTrap's (correct) survival as a regression.
- P2: none new from this gate.

## Overall verdict

CHECKPOINT 5 PASS.

G1, G2, G2b, and G4 all HELD exactly under independent, from-scratch,
worktree-isolated re-measurement. G3 is SPLIT only on a test-name labeling
detail in the prediction text -- the claim it was written to check (an
asymmetric kill pattern proving _ResolveFeatureStrucOwner is a real
compensating layer) is fully confirmed, and M-T8-2 (the other G3 half) HELD
exactly. No mutation went un-killed; no predicted-survivor died; every
zero-change claim carries a named, actually-exercised falsifier. Production
(AllomorphOperations.py) took zero edits in the shared tree -- all mutation
testing happened in three disposable worktrees, each hash-verified restored
and removed, confirmed by `git worktree list` (main tree only) and a silent
`git worktree prune -v`.
