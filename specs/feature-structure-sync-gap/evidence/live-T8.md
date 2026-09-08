# T8 (AllomorphOperations MsEnvFeaturesOA sync, unfiled P0 -- spec.md:655) -- live evidence

Cycle 16. `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`).
T8 is an UNFILED P0 -- no GitHub issue exists; filing one is an outstanding
USER decision. This file references "T8, spec.md:655" only.

Predictions committed verbatim, before any run, at
`specs/feature-structure-sync-gap/evidence/live-T8-predictions.md` (commit
`cf2fdfed`).

## STEP 1 -- hasattr trap measurement (P1, committed as a durable test)

Command:
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_t8_allomorph_feature_sync.py::TestT8LiveHasattrTrap -m requires_live_project -q
```
1 passed. `tests/live_status.json` -> `"run_mode": "live"`.

Bare `sandbox.Object(hvo)` view of a real `MoAffixAllomorph`:
```
ClassName == "MoAffixAllomorph"
hasattr(bare, "Form")            -> False
hasattr(bare, "IsAbstract")      -> False
hasattr(bare, "MorphTypeRA")     -> False
hasattr(bare, "MsEnvFeaturesOA") -> False
```

**P1 (first half): HELD.** Unlike T7's cycle-13 probe (deleted after one run,
losing provenance), this measurement lives in a committed, non-deleted test
(`TestT8LiveHasattrTrap`) that runs every cycle going forward.

### P1 second half -- the PRE-FIX GetSyncableProperties(hvo) claim

Measured directly against the parent commit `09fcbf8` (before this cycle's
production fix), in a disposable worktree (see STEP 4 for the worktree
mechanics), via a throwaway probe file inside that disposable worktree
(the worktree itself -- not a tracked-tree file -- is the disposable unit;
its full stdout is quoted here verbatim rather than left implicit):

```
PRE-FIX bare ClassName: MoAffixAllomorph
PRE-FIX hasattr(bare, 'Form'): False
PRE-FIX hasattr(bare, 'IsAbstract'): False
PRE-FIX hasattr(bare, 'MorphTypeRA'): False
PRE-FIX hasattr(bare, 'MsEnvFeaturesOA'): False
PRE-FIX GetSyncableProperties(hvo) == {'Form': {}, 'MorphTypeRA': None}
1 passed, 6 warnings in 4.00s
```

**P1: HELD in full.** Exact match to the predicted dict
`{"Form": {}, "MorphTypeRA": None}` -- the pre-fix code silently dropped
every property on the HVO entry path with no raise.

## STEP 3 -- post-implementation round-trip evidence

Command:
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_t8_allomorph_feature_sync.py -m requires_live_project -q
```
Result: `6 passed, 21 deselected`. `tests/live_status.json` ->
`"run_mode": "live"`, `"run_timestamp": "2026-09-08T04:08:50Z"`,
`"uncategorized_live_tests": []` (all 6 carry an explicit
`live_phase("AllomorphOperations", "modify")` marker).

### Pre-state / post-state, re-read from the LCM

**`test_ms_env_features_capture_apply_roundtrip`**: `_ApplyFeatureStruc`
attached a real `{feat.Guid: value.Guid}` spec to a fresh `TEST_t8src`
`MoAffixAllomorph`'s `MsEnvFeaturesOA`. Re-fetched via
`sandbox.Object(src_allo.Hvo)` -> `GetSyncableProperties()["MsEnvFeatures"]
["specs"]` matched. `ApplySyncableProperties(tgt_allo, props)` on a
separately-created `TEST_t8tgt` allomorph; re-fetched via a FRESH
`sandbox.Object(tgt_allo.Hvo)` -> same specs. PASS.

**`test_hvo_entry_path_captures_form`** (P1 pin): `GetSyncableProperties(hvo)`
on a freshly created affix allomorph returns a non-empty `"Form"` matching
the already-typed-object capture. PASS -- confirms defects (i)/(ii) fixed.

**`test_apply_raises_on_unresolved_feature_guid`** (C7 real enforcement):
raised `FP_ParameterError` naming the bogus feature GUID. PASS.

**`test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise`**
(P2 live half): real `MoStemAllomorph`, `GetSyncableProperties` returned
neither `MsEnvFeatures` nor `MsEnvFeaturesGuid`, no raise. PASS.

**`test_hvo_path_casts_to_concrete_affix_allomorph`** (direct C2 cast lock):
pre-cast bare object confirmed `not hasattr(..., "MsEnvFeaturesOA")`;
resolved object's `ClassName == "MoAffixAllomorph"`, `.MsEnvFeaturesOA`
directly readable (`None`). PASS.

### Overall pass/fail line

**PASS -- 6/6 live tests green, `run_mode: live`, all six categorized under
`AllomorphOperations`/`modify`.**

## STEP 4 -- P4: comparator delta measured at BOTH commits (disposable worktree)

`git worktree add <tmpdir> HEAD` from commit `016a97a4` (this cycle's test
commit; parent `09fcbf8`). Copied `tests/fixtures/*.fwbackup` read-only into
the worktree's own `tests/fixtures/`. Hash of
`flexicon/code/Lexicon/AllomorphOperations.py` inside the worktree at
`016a97a4`: `6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d` (matches
`git rev-parse HEAD:flexicon/code/Lexicon/AllomorphOperations.py` in the
shared tree). `BaseOperations.py` hash `a8e914bf...` (unchanged since T6b).

### 4a. Wide offline comparator (whole `tests/operations tests/contract`)

Command (both runs, same shell, worktree checked out at each commit in turn):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
```

BEFORE (`09fcbf8`): `2 failed, 416 passed, 518 deselected, 8 warnings`
AFTER (`016a97a4`): `2 failed, 437 passed, 524 deselected, 8 warnings`

Delta: `+21 passed` (the 21 new offline T8 tests), `+6 deselected` (the 6 new
live T8 tests), the SAME 2 failures both times
(`TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception` -- the documented foreign red pair,
unrelated to T8). Matches the comparator baseline exactly (416/2, expected
red set of 2, not 3).

### 4b. Narrow live comparator -- the 9-file wide-instrument set (archivist-confirmed)

Per `specs/feature-structure-sync-gap/reviews/cycle16-archivist-callsites.md`,
only 3 of the 9 floor files carry `requires_live_project` AND touch
`Allomorphs`: `test_allomorphs_live.py`, `test_lexicon_brackets_live.py`
(`TestAllomorphBrackets`), `test_owner_cast_pattern.py`. The other 6 are
offline/mock-style (excluded from live comparison; they cannot flip).

Command (both runs, same shell):
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_allomorphs_live.py tests/operations/test_lexicon_brackets_live.py tests/operations/test_owner_cast_pattern.py -m requires_live_project -q --tb=no -rA
```

BEFORE (`09fcbf8`): `31 passed, 24 deselected, 2 xfailed`
AFTER (`016a97a4`): `31 passed, 24 deselected, 2 xfailed`

Per-test PASSED/FAILED/XFAIL/ERROR line lists, sorted and diffed:
```
diff before_sorted.txt after_sorted.txt
-> (no output -- zero flips)
```

**P4: HELD, MEASURED at both commits (not reasoned).** No pre-existing live
test in the 9-file wide-instrument set flipped in either direction. The
archivist's per-call-site table additionally shows 7 of `Allomorphs`'
11 call sites (`SetFormAudio`, `GetFormAudio`, `GetMorphType`,
`SetMorphType`, `GetPhoneEnv`, `AddPhoneEnv`, `RemovePhoneEnv`) have ZERO
live coverage of any kind -- the C2 cast widening at those sites is
therefore untested by the pre-existing suite (vacuously non-flipping, not
a gap this comparator can surface); this is noted, not hidden.

## STEP 5 -- mutation testing (disposable worktree, same instance as STEP 4)

Worktree removed with `git worktree remove --force <tmpdir>` after both
mutations were reverted and hash-verified; a final offline run inside the
worktree (`21 passed, 6 deselected`) confirmed the restore before removal.
`git status --porcelain` in the shared tree showed no trace of the worktree
afterward (unchanged from before the worktree was created).

| # | Mutation | Killed (tests) | Survived (relevant tests) | Restore hash-verified |
|---|---|---|---|---|
| M-T8-1 | `__GetAllomorphObject`: cast removed, unconditional `return obj` | live: `TestT8LiveDirectCast::test_hvo_path_casts_to_concrete_affix_allomorph`, `TestT8LiveRoundTrip::test_hvo_entry_path_captures_form` | live: `test_ms_env_features_capture_apply_roundtrip`, `test_apply_raises_on_unresolved_feature_guid`, `test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise`, `TestT8LiveHasattrTrap` -- all SURVIVED | yes -- `6a0c6e94...` restored |
| M-T8-2 | `GetSyncableProperties`: `if class_name == "MoAffixAllomorph":` guard removed, resolver called unconditionally | offline: `test_capture_stem_allomorph_returns_no_feature_keys_and_never_calls_resolver`, `test_capture_unknown_class_name_returns_no_feature_keys_and_never_calls_resolver`. live: `TestT8LiveStemAllomorphNoFeatureKeys::test_real_live_stem_allomorph_capture_emits_no_feature_keys_and_does_not_raise` -- failed with `FP_ParameterError: _ResolveFeatureStrucOwner: ClassName 'MoStemAllomorph' is not a recognized feature-structure owner...` | -- | yes -- `6a0c6e94...` restored |

**P5 adjudication: HELD.** M-T8-1 kills exactly the split predicted: the
direct cast test AND the HVO-entry Form-capture test die, while the
`MsEnvFeaturesOA` round-trip (which routes through
`_ResolveFeatureStrucOwner`'s own internal cast -- a second compensating
layer) survives, along with the C7-raise and stem-no-raise tests.

**P2 adjudication: HELD.** Unmutated: real live `MoStemAllomorph` capture
neither raises nor emits feature keys. Under M-T8-2: the same test FAILS
with `FP_ParameterError` naming `MoStemAllomorph`, exactly as predicted.

**P3 adjudication: HELD by static lock.**
`test_no_non_none_slot_literal_anywhere_in_feature_struct_calls` confirms no
`slot="..."` literal (other than `None`) appears in
`GetSyncableProperties`/`ApplySyncableProperties`/
`__CaptureFeatureStrucProp`/`__ApplyFeatureStrucProp`. `MoAffixAllomorph`
has exactly one C1 row (`Shared/lcm_constants.py:131-133`), so no slot
disambiguation test exists or is needed (R16-1).

## Comparator baseline cross-check

Full-suite run (STEP 4a) reproduces the documented comparator baseline
(416 passed / 2 failed pre-existing, expected red set of 2 -- the foreign
`TestPhase2JoinOrOpen` pair, not 3) at the parent commit, and shows only
additive change (+21/+6, 0 regressions) at the T8 commit.

## Summary

| Prediction | Verdict | Backing |
|---|---|---|
| P1 | HELD | Durable committed test (bare hasattr) + disposable-worktree pre-fix probe, exact dict match |
| P2 | HELD | Real (non-mocked) offline resolver test + live no-raise test + M-T8-2 mutation (live FAILED naming MoStemAllomorph) |
| P3 | HELD | Static AST/source lock, no non-None slot= literal found |
| P4 | HELD, measured at both commits | Wide offline comparator (+21/+6, 0 regressions) + narrow live comparator over the archivist-confirmed 9-file set (zero flips, diffed) |
| P5 | HELD | M-T8-1 mutation: direct-cast + HVO-entry tests killed, round-trip survives |

No prediction required a STOP/needs_human escalation. All five predictions
HELD -- none falsified this cycle.
