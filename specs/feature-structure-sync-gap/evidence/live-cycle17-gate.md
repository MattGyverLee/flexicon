# Live verification -- cycle-17 Checkpoint 5 INDEPENDENT gate (measurement half)

**Project:** Target sandbox (`target_sandbox`, tempdir copy) | **Fixture:** tests/fixtures/"Target 2026-07-06 0218.fwbackup"
**Verifier:** independent verification agent, did NOT implement T8, ran everything from scratch in disposable worktrees.
**HEAD at gate start:** e6623788 (verified `git diff --stat e7f1048..HEAD` -- only 3 docs files under specs/, no code touched)
**Date:** 2026-09-08

## Claim under test
Cycle-16/17 predictions G1-G4 (G5 already adjudicated by the archivist, not
redone here). This gate independently re-runs every mutation from scratch in
isolated worktrees per the BINDING worktree-isolation rule (cycle 8).

---

## LEG 4a -- baseline BEFORE new tests (run twice, same command)

Command:
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider
```
Run 1: 2 failed, 437 passed, 524 deselected, 8 warnings in 4.07s
Run 2: 2 failed, 437 passed, 524 deselected, 8 warnings in 3.60s

Failing node IDs (both runs, identical):
- tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
- tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception

No third failure. G4 baseline HELD exactly.

---

## LEG 1 -- P4's unmeasured HVO axis (G1)

New file (committed to shared tree, HEAD 44c67eb0):
tests/operations/test_t8_hvo_path_gate.py -- TestHvoPathCastGetForm (primary
site, GetForm :813, read-only) and TestHvoPathCastSetForm (second covered
site, SetForm :858, mutates -- sandbox only). Both pass a genuine Python
int (allo.Hvo), asserted isinstance(hvo, int) before the call.

### (b) Live run at HEAD 44c67eb0, shared tree, target_sandbox
Command:
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_t8_hvo_path_gate.py -m requires_live_project -q -p no:cacheprovider
```
Result: 2 passed, 12 warnings in 4.09s

tests/live_status.json (full verbatim block):
```
{
  "by_class": {
    "AllomorphOperations": {
      "add": { "last_verified": null, "status": "untested", "tests": [] },
      "delete": { "last_verified": null, "status": "untested", "tests": [] },
      "modify": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastSetForm::test_set_form_via_genuine_hvo_int_writes_through_concrete_form"
        ]
      },
      "read": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastGetForm::test_get_form_via_genuine_hvo_int_reads_concrete_form"
        ]
      },
      "reorder": { "last_verified": null, "status": "untested", "tests": [] }
    }
  },
  "by_test": {
    "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastGetForm::test_get_form_via_genuine_hvo_int_reads_concrete_form": {
      "duration_seconds": 0.174, "operations_class": "AllomorphOperations", "phase": "read", "status": "pass"
    },
    "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastSetForm::test_set_form_via_genuine_hvo_int_writes_through_concrete_form": {
      "duration_seconds": 0.025, "operations_class": "AllomorphOperations", "phase": "modify", "status": "pass"
    }
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T14:21:48Z",
  "uncategorized_live_tests": []
}
```
run_mode: live CONFIRMED.

Pre-state (read from LCM): new TEST_gform allomorph created on a fresh
TEST_ entry; hvo = genuine int (entry-scoped HVO, e.g. ~10441); bare
sandbox.Object(hvo) confirmed not hasattr(bare, "Form") (P1 precondition
re-confirmed live).
Post-state (re-queried from LCM): GetForm(hvo) returned "TEST_gform";
SetForm(hvo, "TEST_sform_new") then GetForm(sandbox.Object(hvo)) (fresh
re-fetch) returned "TEST_sform_new".
Cleanup: both tests delete their TEST_ entry in a finally: block on a
tempdir sandbox -- nothing persisted to the real Target.

### (c) Worktree mutation M-G1
Worktree: .../scratchpad/wt-leg1 at HEAD 44c67eb0.
Pre-mutation hash: git hash-object flexicon/code/Lexicon/AllomorphOperations.py
= 6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d, matches
git cat-file -p HEAD:...|git hash-object --stdin (identical) -- worktree
verified clean before mutating.

Mutation: replaced the class_name = getattr(...) + two if/elif cast
branches at :1364-1369 with "return obj" unchanged.

Live run (same command, same test file, mutated worktree):
2 failed, 12 warnings in 4.55s

Failure 1 (GetForm): flexicon\code\Lexicon\AllomorphOperations.py:854:
AttributeError: 'ICmObject' object has no attribute 'Form'
Failure 2 (SetForm): flexicon\code\Lexicon\AllomorphOperations.py:906:
AttributeError: 'ICmObject' object has no attribute 'Form'

tests/live_status.json after mutation run (full verbatim block):
```
{
  "by_class": {
    "AllomorphOperations": {
      "add": { "last_verified": null, "status": "untested", "tests": [] },
      "delete": { "last_verified": null, "status": "untested", "tests": [] },
      "modify": {
        "last_verified": null, "status": "fail",
        "tests": ["tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastSetForm::test_set_form_via_genuine_hvo_int_writes_through_concrete_form"]
      },
      "read": {
        "last_verified": null, "status": "fail",
        "tests": ["tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastGetForm::test_get_form_via_genuine_hvo_int_reads_concrete_form"]
      },
      "reorder": { "last_verified": null, "status": "untested", "tests": [] }
    }
  },
  "by_test": {
    "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastGetForm::test_get_form_via_genuine_hvo_int_reads_concrete_form": {
      "duration_seconds": 0.182, "operations_class": "AllomorphOperations", "phase": "read", "status": "fail"
    },
    "tests/operations/test_t8_hvo_path_gate.py::TestHvoPathCastSetForm::test_set_form_via_genuine_hvo_int_writes_through_concrete_form": {
      "duration_seconds": 0.026, "operations_class": "AllomorphOperations", "phase": "modify", "status": "fail"
    }
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T14:23:18Z",
  "uncategorized_live_tests": []
}
```

Both went RED under M-G1, matching the falsifiable prediction. G1: HELD.
No need for a second covered site.

Restore: git checkout -- flexicon/code/Lexicon/AllomorphOperations.py
inside the worktree (NOT the shared tree); post-restore hash
6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d == pre-mutation hash. git status
--porcelain empty.

Worktree removed: git worktree remove <wt-leg1> --force; confirmed by
git worktree list (main tree only) and silent git worktree prune -v.

---

## LEG 2 -- surviving hasattr gates (G2, G2b)

### (a) Live measurement (disposable probe, never committed)
Probe file tests/operations/_leg2_probe_disposable.py created in the shared
tree, run live, then deleted (index confirmed empty both before and after
via git status --porcelain --untracked-files=no).

Command:
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/_leg2_probe_disposable.py -m requires_live_project -q -p no:cacheprovider -s
```
Stdout (verbatim):
```
PRE: entry.ClassName = LexEntry hvo= 10442
RESULT (no raise): {'Form': {}, 'MorphTypeRA': None}
RESULT == expected: True
1 passed, 5 warnings in 3.60s
```
Object used: sandbox.LexEntry.Create("TEST_leg2_probe"), ClassName ==
"LexEntry" (neither MoStemAllomorph nor MoAffixAllomorph), per the
archivist's recommendation. Deleted in a finally: block.

G2: HELD exactly -- no raise, dict is exactly {'Form': {}, 'MorphTypeRA':
None}.

### (b) Lead ruling followed
Per the BINDING ruling, no durable test asserts this silent-drop shape as
expected behaviour. The measurement above is recorded here (evidence file)
only; it is NOT pinned by any committed test.

### (c) New allowlist test
tests/operations/test_t8_allomorph_hasattr_allowlist.py (committed,
14dce753): ast.walk over the WHOLE module, filtered by first-argument
identity (Name.id == "allomorph"), asserting the resulting set is exactly
{(GetSyncableProperties,Form), (GetSyncableProperties,IsAbstract),
(GetSyncableProperties,MorphTypeRA)}, count == 3. A second, non-gating
documentation test independently counts total hasattr calls in the module
== 7 (4 owner/parent in Delete/Duplicate + 3 allomorph-scoped).

Offline run at HEAD 14dce753: 2 passed in 1.12s.

G2b: HELD (7 total, not 3; 3 allomorph-scoped exactly as specified).

### (d) Killing-mutation proof (non-tautological)
Worktree .../scratchpad/wt-leg2 at HEAD 14dce753.
Pre-mutation hash: 6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d (matches
committed blob).

Mutation: inserted "if hasattr(allomorph, 'MsEnvFeaturesOA'): pass" inside
GetForm (per the archivist's specification -- deliberately NOT inside
GetSyncableProperties, to prove the module-wide scope, not a
function-list scope).

New allowlist test under mutation: 2 failed --
"AssertionError: Total hasattr() call count in AllomorphOperations.py
changed: 8 (expected 7 ...)" and the count==3 assertion also fails with
the new 4th call surfaced in its message.

Control: the SHIPPED per-function test file
(test_t8_allomorph_feature_sync.py, offline) under the SAME mutation:
21 passed, 6 deselected -- stays fully GREEN, confirming the gap the new
test closes (the shipped test enumerates GetSyncableProperties and 4
other named functions only; it never looks inside GetForm).

Restore: git checkout -- inside worktree; post-restore hash
6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d == pre-mutation hash, git status
--porcelain empty.

Worktree removed; git worktree list main-only; git worktree prune -v
silent.

---

## LEG 3 -- independent reproduction (G3), FROM SCRATCH

Worktree .../scratchpad/wt-leg3 at HEAD 14dce753, fixture copied
read-only, pre-mutation hash 6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d
(matches committed blob).

### Baseline (unmutated worktree)
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_t8_allomorph_feature_sync.py -m requires_live_project -q -p no:cacheprovider
```
6 passed, 21 deselected, 51 warnings in 5.70s -- all four shipped live
classes pass at HEAD.

### M-T8-1 (remove the cast, same edit as M-G1)
Live run, same command: 2 failed, 4 passed, 21 deselected, 51 warnings in 5.85s

Actual dead set:
- TestT8LiveDirectCast::test_hvo_path_casts_to_concrete_affix_allomorph --
  AttributeError: 'ICmObject' object has no attribute 'MsEnvFeaturesOA'
  (assertion at test_t8_allomorph_feature_sync.py:879)
- TestT8LiveRoundTrip::test_hvo_entry_path_captures_form --
  AssertionError: Defects (i)/(ii): HVO entry path silently dropped Form.

Survived: TestT8LiveHasattrTrap::test_bare_moaffixallomorph_hasattr_all_four_false,
TestT8LiveRoundTrip::test_ms_env_features_capture_apply_roundtrip,
TestT8LiveRoundTrip::test_apply_raises_on_unresolved_feature_guid,
TestT8LiveStemAllomorphNoFeatureKeys::test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise.

DISCREPANCY vs. the literal prediction text: G3 predicted the dead set by
NAME as {TestT8LiveDirectCast, TestT8LiveHasattrTrap}. The class named
TestT8LiveHasattrTrap (its one test,
test_bare_moaffixallomorph_hasattr_all_four_false) does NOT call
__GetAllomorphObject at all -- it reads sandbox.Object(hvo) directly and
asserts hasattr is False on the BARE object, which is structurally
independent of the cast and cannot be affected by M-T8-1. It is therefore
CORRECTLY unaffected, not a resilience finding. The test that actually
exercises the HVO-entry Form-capture path and DOES die is
TestT8LiveRoundTrip::test_hvo_entry_path_captures_form -- a different
class than the one named in the prediction. Read literally,
TestT8LiveHasattrTrap (predicted-dead) surviving triggers G3's falsifier
by name; read substantively, the underlying claim (asymmetric split:
direct-cast dies, HVO-entry-Form-capture dies, round-trip survives) is
fully confirmed, just against a differently-named test. Adjudicated as
SPLIT below, not silently reasoned away.

Collateral (disclosed): re-applying M-T8-1 and running the FULL offline
suite of test_t8_allomorph_feature_sync.py also kills
TestAllomorphSyncStatic::test_get_allomorph_object_casts_on_classname_and_never_raises
(a Section A static source-pattern test) -- 1 failed, 20 passed, 6
deselected. This is an EXTRA kill (the source-pattern test correctly
detects the removed cast lines), not a not-killed mutation; disclosed per
instruction, not hidden.

Restore + hash-verify: 6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d (both
after the live-only restore check and after the collateral-check restore).

### M-T8-2 (delete the ClassName == "MoAffixAllomorph" guard at :594)
Live run: 1 failed, 5 passed, 21 deselected, 51 warnings in 5.18s

Only failure: TestT8LiveStemAllomorphNoFeatureKeys::test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise

Exact message:
```
flexicon.code.exceptions.FP_ParameterError: _ResolveFeatureStrucOwner:
ClassName 'MoStemAllomorph' is not a recognized feature-structure owner.
Supported ClassNames: MoAffixAllomorph, MoDerivAffMsa, MoInflAffMsa,
MoStemMsa, PartOfSpeech, PhNCFeatures, PhPhoneme, WfiAnalysis.
```
Names MoStemAllomorph exactly as predicted. No other test affected.
M-T8-2 half of G3: HELD exactly.

Restore + hash-verify: git checkout -- inside worktree; post-restore hash
6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d == committed blob, git status
--porcelain empty.

Worktree removed; git worktree list main-only; git worktree prune -v
silent.

---

## LEG 4b -- after the gate's own new tests land (run twice)

Command (same as LEG 4a, same shell, shared tree, HEAD 14dce753):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider
```
Run 1: 2 failed, 439 passed, 526 deselected, 8 warnings in 3.85s
Run 2: 2 failed, 439 passed, 526 deselected, 8 warnings in 3.73s

Same red set as LEG 4a (TestPhase2JoinOrOpen x2), unchanged.

Arithmetic: passed 437 -> 439 = +2, exactly the 2 new OFFLINE tests in
tests/operations/test_t8_allomorph_hasattr_allowlist.py.
deselected 524 -> 526 = +2, exactly the 2 new LIVE tests in
tests/operations/test_t8_hvo_path_gate.py (live-marked, so they land in
deselected under -m "not requires_live_project", not in passed).
failed unchanged at 2. Fully explained, no unexplained movement.

---

## Cleanup confirmation
git worktree list (final): D:/Github/_Projects/_LEX/flexicon  14dce75
[main] -- main tree only.
git worktree prune -v (final): silent, no output.
git status --porcelain --untracked-files=no (final): only the
pre-existing "D .claude/ralph-loop.local.md" -- untouched, as instructed.
No git add -A / -u / commit -a used anywhere in this gate.

## Result summary
| Leg | Result |
|---|---|
| LEG 4a (baseline) | PASS -- G4 HELD exactly, 2/437/524, red set exact |
| LEG 1 (HVO axis) | PASS -- G1 HELD, both new tests RED under M-G1, restored+hash-verified |
| LEG 2 (hasattr gates) | PASS -- G2 HELD exactly, G2b HELD, allowlist test proven non-tautological |
| LEG 3 (independent repro) | SPLIT -- M-T8-1 and M-T8-2 substantively HELD; G3's literal test-name mapping for the "HVO-entry" death is wrong (TestT8LiveHasattrTrap vs. actual TestT8LiveRoundTrip::test_hvo_entry_path_captures_form) |
| LEG 4b (post-gate delta) | PASS -- delta fully explained, 2 failed unchanged |
