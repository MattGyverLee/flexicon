# Live verification -- cycle-4 gate, T4

**Project:** Target (real, in-place; restore_target.py --check confirmed
present, not locked) for the live subset; disposable git worktrees at
a26d39c (T4's true parent) and current HEAD (e17cd7d) for offline
before/after comparison.
**Command (live subset, exact, as specified):**
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_natural_class_feature_sync.py tests/operations/test_natural_classes.py tests/operations/test_phonemes.py tests/operations/test_apply_feature_struc.py -m requires_live_project -q
```
**run_mode:** live (confirmed via tests/live_status.json after every live
run in this session).
**Date:** 2026-09-07

## Claim under test
T4 extracts BaseOperations._ApplyFeatureStruc and re-points NC
(on_unresolved="raise") / Phoneme (on_unresolved="skip") at it as thin
call-throughs, with zero runtime behaviour change, plus new coverage for
the previously-untested C4 dict shape and nested recursion.

## A. Live subset -- HEAD (e17cd7d) vs pre-T4 parent (a26d39c)
| Commit | Cmd | Result |
|---|---|---|
| a26d39c (pre-T4) | 3 named files | 34 passed, 14 deselected, 1 failed |
| e17cd7d (HEAD) | 3 named files | 34 passed, 14 deselected, 1 failed (identical) |
| e17cd7d (HEAD) | all 4 files incl new test_apply_feature_struc.py | 41 passed (34+7 new), 14 deselected, 1 failed |

The one failure both sides: test_natural_classes.py::TestNaturalClassSync::
test_apply_raises_on_type_mismatch_segments_target, AttributeError:
'ICmObject' object has no attribute 'Name' at NaturalClassOperations.py:1270
(matches implementer's evidence). Confirmed this line is the type-mismatch
GUARD (if nc.ClassName != "PhNCFeatures":) ABOVE __ApplyFeatures; git diff
a26d39c 4aca74a -- NaturalClassOperations.py shows only __ApplyFeatures /
__ResolveByGuid changed. Pre-existing, identical both sides.

## B. Offline suite narrowed to the 4 task files (clean, both sides)
| Commit | Cmd | Result |
|---|---|---|
| a26d39c | offline, 3 files | 14 passed, 35 deselected |
| e17cd7d | offline, 4 files | 14 passed, 42 deselected (+7 new test file) |

## C. Full-repo offline suite (python -m pytest -m "not requires_live_project" -q, literal command, no path arg)
This crashes identically on BOTH sides, and is PRE-EXISTING, unrelated to
T4. Root cause isolated: tests/conftest.py's session-scoped autouse
initialize_flex_for_tests fixture calls a raw, UNGUARDED
Sldr.Initialize(True) (unlike the shared FLExInit.FLExInitialize(), which
wraps the identical call in try/except specifically because "SLDR may
already be initialized in some test/startup scenarios"). When any module
that independently calls FLExInitialize()/inits SLDR runs first in
collection order (several legacy flexicon/tests/, flexicon/sync/tests/
modules do this in setUpModule; tests/contract/test_lcm_contract.py's
TestLiveContractVerification fixture chain does too), the conftest
fixture's own later Sldr.Initialize(True) raises
System.InvalidOperationException: The SLDR has already been initialized,
uncaught, which fails the session fixture and cascades an ERROR into
every other test depending on it (hundreds).

Measured both sides to confirm this is orthogonal to T4:
| Commit | Result |
|---|---|
| a26d39c (pre-T4) | 225 passed, 612 deselected, 1270 errors (same crash) |
| e17cd7d (HEAD) | 225 passed, 627 deselected, 1273 errors (same crash; +15 deselected fully accounted for by new/concurrent test files) |

Delta between the two (+15 deselected, +3 errors, matching 15
newly-collected requires_live_project-marked tests from
test_apply_feature_struc.py [7] and the concurrent session's
test_name_field_identity_probe.py [8]) is fully consistent with zero T4
regression. The implementer's reported "1495 passed, 3 failed" figure for
this exact bare command did NOT reproduce in this environment -- flagged
below as a discrepancy, but it does not change the T4 verdict because
(a) the crash is proven pre-existing at a26d39c, before any T4 commit
exists, and (b) it is orthogonal: nothing in T4's diff touches
tests/conftest.py, flexicon/sync/tests/, or flexicon/tests/.

**Discrepancy flagged for the lead:** the clean "1495 passed / 3 failed"
number in the implementer's evidence could not be reproduced in this
session on this machine; the same command instead throws the
SLDR-double-init cascade above, identically on both sides of T4. This is
an environmental/ordering hazard (likely dependent on OS-level DLL state,
process history, or filesystem enumeration order), pre-existing in the
repo, not introduced or hidden by T4. Recommend a follow-up ticket for
tests/conftest.py's unguarded Sldr.Initialize(True) (should route through
FLExInitialize() or mirror its try/except) and for
flexicon/sync/tests/test_base_operations.py lacking the
requires_live_project marker its sibling test_duplicate_operations.py was
explicitly given for exactly this failure mode.

## Mutation test 1 -- legacy raise-mode branch
Changed BaseOperations.py's _ApplyFeatureStruc, legacy-list raise-mode
branch (if feat_obj is None: raise FP_ParameterError(...) -> continue).
Re-ran the live subset: 3 failed (up from 1) --
test_apply_raises_on_missing_target_feature_guid,
test_apply_raises_on_type_mismatch_segments_target (pre-existing),
test_apply_raise_mode_raises_on_unresolved_feature_guid. Confirms the
raise-mode tests exercise real, load-bearing code, not a tautology.

Restored from saved copy; hash-verified:
git hash-object flexicon/code/BaseOperations.py ==
1bc956bbb629f217f9bd8051d47f5af9dbbdb568 ==
git rev-parse HEAD:flexicon/code/BaseOperations.py. Byte-identical.

## Mutation test 2 -- nested recursion path (_ApplyFeatureStrucSpecMap)
Changed the per-level TypeRA assignment inside the transaction from
struct.TypeRA = type_obj to pass (silently drops the per-level type).
Re-ran tests/operations/test_apply_feature_struc.py live: 1 failed --
test_apply_nested_c4_dict_creates_complex_value_and_recurses (the
implementer's own "first live proof of nested recursion" test), 6 passed.
Confirms this path is genuinely exercised, not dead code the tests happen
to walk past.

Restored; hash-verified identical again: git hash-object ==
1bc956bbb629f217f9bd8051d47f5af9dbbdb568 (same blob hash both times).
Re-ran live subset post-restore: back to 1 known failure, 26 passed.

## Zero-delta / C1-C7 audit (code-level, diffed and read)
- PhonemeOperations.py:1351 (hasattr(phoneme, "FeaturesOA") and
  phoneme.FeaturesOA), :1431 (if features:) -- both present, byte
  identical; git diff a26d39c 4aca74a -- PhonemeOperations.py shows only
  __ApplyFeatures's signature (dropped fill_gaps) and body (now a
  call-through) changed; :1428/:1431/:1351/__ApplyBasicIPASymbol untouched.
- Phoneme's __ApplyFeatures call-through passes on_unresolved="skip"
  (line 1493); NC's passes on_unresolved="raise" and
  struct_guid=features_guid (preserved).
- Neither NC nor Phoneme drives the C4 dict branch: both still build/pass
  a plain list of {"FeatureGuid","ValueGuid"} dicts (capture sides
  unmodified by T4 -- no diff hunks touch GetSyncableProperties).
- Exactly ONE copy of the C1 table repo-wide: FEATURE_STRUC_OWNER_TABLE
  defined once in flexicon/code/Shared/lcm_constants.py; other hits
  (BaseOperations.py, test file) are imports/usages only.

## E5 assertion-migration audit (independent enumeration)
Enumerated pre-T4 (git show a26d39c:tests/operations/test_natural_class_feature_sync.py)
vs current file. 6 individual assert statements (grouped by spec's own
convention into "5 shape assertions"), all present 1:1 post-T4, none
deleted or weakened:

| # | Assertion | Pre-T4 target | Post-T4 target |
|---|---|---|---|
| 1 | "raise FP_ParameterError" in src | NC __ApplyFeatures | BaseOperations._ApplyFeatureStruc via new _base_method_source, line 169 |
| 2 | "feat_obj is None" and "raise" in src | same | same, line 174 |
| 3 | "val_obj is None" in src | same | same, line 178 |
| 4 | unresolved-section slice, no continue before val resolve | literal self.__ResolveByGuid | literal self._ResolveFsByGuid, lines 191-192 |
| 5 | "{feat_guid}" in message | same | same, line 209 |
| 6 | "{nc_name}" in message | same | renamed "{label}" per C5 frozen name; NC's rendered text unchanged (label=f"natural class '{nc_name}'"), line 213 |

test_no_hasattr_gate_on_subtype_only_members's apply_features_src still
points at NC's own thin call-through (correctly left alone, not weakened).

## C4a dual-shape / C5-C7 code confirmation
Read _ApplyFeatureStruc (BaseOperations.py:1999-2246) and
_ApplyFeatureStrucSpecMap (:2247-) directly: isinstance(spec_dict, dict)
branches to the recursion helper (C4 dict); else the legacy per-item loop
runs, byte-equivalent to pre-T4 NC/Phoneme bodies (idempotency set, lazy
val resolution in raise-mode, resolve-both-then-check in skip-mode,
partial-application-on-raise semantics preserved). Legacy shape has
dedicated live coverage (TestApplyFeatureStrucLegacyListLive, 4 tests);
C4 dict shape has separate dedicated live coverage
(TestApplyFeatureStrucC4DictLive, 3 tests, including one level of
nesting).

## Part 6 -- opportunistic finding, NOT fixed (per instruction)
PhonemeOperations.__ApplyBasicIPASymbol (current location:
PhonemeOperations.py:1434-1452, specifically lines 1440-1442) builds its
own {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()} map
and resolves WS handles itself, rather than delegating to
_apply_props_loop. Confirmed via git diff a26d39c 4aca74a --
PhonemeOperations.py that this method is completely untouched by T4.
Answer: YES, this apply-side WS-map build exists and will NOT inherit a
fix queued as issue #250 Defect 4. Not changed, per instruction.

## Result
[PASS] -- T4's zero-runtime-delta claim holds under live and offline
re-measurement (both narrowed and, so far as the crash allows, full-repo);
the E5 migration is complete and 1:1; both mutation tests prove the tests
are load-bearing, not tautological; C1-C7 contract items are satisfied at
the code level. One documented discrepancy (implementer's reported clean
full-suite "1495 passed" count did not reproduce here) is explained as a
pre-existing, order-dependent environmental crash identical on both sides
of T4, not a T4 defect.
