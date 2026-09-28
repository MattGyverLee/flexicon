# T7 (POSOperations feature-struct sync, flexicon#252) -- live evidence

Cycle 13. `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`).

## STEP 0 -- pre-modification probe (adjudicates P1, P3)

Command (disposable probe file, deleted after this record was written):

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_t7_probe_disposable.py -m requires_live_project -q -s
```

`tests/live_status.json` -> `"run_mode": "live"`, 1 passed.

Sandbox contained 5 POS (first: "Adverb", hvo=2706). Note: cycle-1's probe
recorded 26 POS; this sandbox snapshot has 5. Does not affect the P1/P3
adjudication (existence/type/presence checks, not a count claim).

### (a) P1 adjudication

```
GetSyncableProperties(hvo=2706)        -> {}                       (0/4 keys)
GetSyncableProperties(<typed POS obj>) -> keys ['Abbreviation', 'CatalogSourceId',
                                                'Description', 'Name']  (4/4 keys)
```

**P1: HELD.** The HVO entry path returns an empty dict at unmodified HEAD;
the already-typed-object entry path (as yielded by `GetAll()`) returns all
four keys. Confirms the entry-path-conditional bug: cycle 1's "hasattr
works on every object GetSyncableProperties will ever receive" conclusion
is true only for the `GetAll()` path.

### (b) P3 adjudication

```
hasattr(IPartOfSpeech, "DefaultFeaturesOA") = True
hasattr(IPartOfSpeech, "InherFeatValOA")    = True
DefaultFeaturesOA declared CLR type = SIL.LCModel.IFsFeatStruc
InherFeatValOA declared CLR type    = SIL.LCModel.IFsFeatStruc
non-null DefaultFeaturesOA count = 0/5
non-null InherFeatValOA count    = 0/5
```

**P3: HELD.** Both properties exist on `IPartOfSpeech`, both declared
`IFsFeatStruc`, and no sandbox POS carries a non-null struct for either --
the live round-trip test must CREATE its struct via the apply path first
(cannot read a pre-existing populated POS).

Neither property was absent, so no STOP/needs_human trigger.

## STEP 3 -- post-implementation round-trip evidence

Command:

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue252_pos_feature_sync.py -m requires_live_project -q
```

Result: `6 passed, 20 deselected`. `tests/live_status.json` ->
`"run_mode": "live"`, `"uncategorized_live_tests": []`
(all 6 carry an explicit `live_phase("POSOperations", "modify")` marker,
avoiding the D4-T7 defect named in the dispatch).

### Pre-state / post-state, re-read from the LCM (never the write-time reference)

**`test_default_features_slot_capture_apply_roundtrip`** (slot="Default"):
- Pre: `_ApplyFeatureStruc(src_pos, "DefaultFeaturesOA", [{"FeatureGuid":
  <feat.Guid>, "ValueGuid": <value.Guid>}])` on a fresh `TEST_252_default_src`
  POS. Re-fetched via `sandbox.Object(src_pos.Hvo)` ->
  `GetSyncableProperties()["DefaultFeatures"]["specs"] ==
  {<feat.Guid>: <value.Guid>}`. PASS.
- Post: `ApplySyncableProperties(tgt_pos, props)` on a separately-created
  `TEST_252_default_tgt` POS. Re-fetched via a FRESH
  `sandbox.Object(tgt_pos.Hvo)` -> `GetSyncableProperties()["DefaultFeatures"]
  ["specs"]` equals the SAME dict. PASS.

**`test_inher_feat_val_slot_capture_apply_roundtrip`** (slot="InherFeatVal"):
same shape, `InherFeatValOA`, both src/tgt re-fetches match. PASS.

**`test_hvo_entry_path_captures_name`** (P1 pin): `GetSyncableProperties(hvo)`
on a freshly created POS returns `"Name"` in its keys, matching
`GetSyncableProperties(<typed obj>)["Name"]`. PASS -- confirms the
`__ResolveObject` cast fixes the silent Name/Abbreviation/Description/
CatalogSourceId drop on the HVO entry path, not just the two new
feature-struct keys.

**`test_apply_raises_on_unresolved_feature_guid`** (C7 real enforcement):
`ApplySyncableProperties` with a bogus feature/value GUID pair raises
`FP_ParameterError` naming the bogus feature GUID. PASS.

**`test_ambiguous_owner_without_slot_raises`** (slot-ambiguity, T14a-style):
`sandbox.POS._ResolveFeatureStrucOwner(pos_obj)` (no `slot=`) raised
`FP_ParameterError` naming both `"PartOfSpeech"` and `"slot"`. Re-fetch via
a fresh `IPartOfSpeech(sandbox.Object(hvo))` showed `DefaultFeaturesOA is
None` and `InherFeatValOA is None` -- no partial attach. PASS.

**`test_hvo_path_casts_to_concrete_pos`** (direct C2 cast lock): the
pre-cast bare object (`sandbox.Object(hvo)`) confirmed
`not hasattr(..., "DefaultFeaturesOA")`; the resolved object's
`ClassName == "PartOfSpeech"` and `.DefaultFeaturesOA`/`.InherFeatValOA`
were directly readable (both `None`, since nothing was attached to this
particular POS). PASS.

### Overall pass/fail line

**PASS -- 6/6 live tests green, `run_mode: live`, all six categorized under
`POSOperations`/`modify`.**

## STEP 4 -- mutation testing (disposable worktree, cycle12-lead-ruling-3)

`git worktree add <tmpdir> HEAD` from commit `4b746a03` (this cycle's test
commit). Copied `tests/fixtures/Target 2026-07-06 0218.fwbackup` read-only
(`chmod 444`) into the worktree's own `tests/fixtures/`. Pre-mutation hash
of `flexicon/code/Grammar/POSOperations.py` inside the worktree:
`f94b4d97efb54ac9f78a1a1c5b3a034303bac951` (matches `git rev-parse
HEAD:flexicon/code/Grammar/POSOperations.py` in the shared tree).
Pre-mutation hash of `flexicon/code/BaseOperations.py`:
`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db` (unchanged since T6b).

| # | Mutation | Killed (tests) | Survived (relevant tests) | Restore hash-verified |
|---|---|---|---|---|
| M1 | `__ResolveObject`: cast removed, unconditional `return obj` | offline: `test_resolve_object_casts_on_classname_and_never_raises`. live: `TestPOSSyncLiveResolveObjectCast::test_hvo_path_casts_to_concrete_pos` (`AttributeError: 'ICmObject' object has no attribute 'DefaultFeaturesOA'`), `TestPOSSyncLiveRoundTrip::test_hvo_entry_path_captures_name` (`assert 'Name' in {}`) | live: `test_default_features_slot_capture_apply_roundtrip`, `test_inher_feat_val_slot_capture_apply_roundtrip`, `test_apply_raises_on_unresolved_feature_guid`, `test_ambiguous_owner_without_slot_raises` -- all 4 SURVIVED | yes -- `f94b4d97...` restored |
| M2 | `__ApplyFeatureStrucProp`: presence gate -> truthiness (`if props.get(key) or props.get(guid_key):`) | offline: `test_apply_gates_on_key_presence_not_truthiness` (source lock), `test_falsy_but_present_feature_struct_key_still_triggers_apply`, `test_falsy_but_present_guid_only_key_still_triggers_apply` | offline: `test_guid_only_present_still_triggers_apply_with_empty_spec`, `test_neither_key_present_never_calls_apply_feature_struc` -- both SURVIVED (truthy-guid fixtures cannot separate presence from truthiness, same T6b finding) | yes -- `f94b4d97...` restored |
| M3 | `__ApplyFeatureStrucProp`: `on_unresolved="raise"` -> `"skip"` | offline: `test_apply_propagates_fp_parameter_error_and_passes_raise_policy`. live: `test_apply_raises_on_unresolved_feature_guid` (real C7 enforcement) | -- | yes -- `f94b4d97...` restored |
| M4 | `BaseOperations._ResolveFeatureStrucOwner`: ambiguous-no-slot picks `rows[0]` instead of raising | live: `TestPOSSyncLiveSlotAmbiguityNoSlot::test_ambiguous_owner_without_slot_raises` | (T14a's own MoDerivAffMsa raise test would also die under this same shared-code mutation -- not re-run here, out of T7's file, noted for completeness) | yes -- `a8e914bf...` restored |
| M5 | `GetSyncableProperties`/`ApplySyncableProperties`: `slot="InherFeatVal"` calls forced to `slot="Default"` | offline: `test_capture_both_slots_populated`, `test_capture_only_one_slot_populated`, `test_apply_dispatches_both_slots_with_correct_prop_names`. live: `test_inher_feat_val_slot_capture_apply_roundtrip` | live: `test_default_features_slot_capture_apply_roundtrip` SURVIVED (only the Default slot is populated in that test, so mis-routing InherFeatVal to the same slot is invisible to it) | yes -- `f94b4d97...` restored |

Worktree removed with `git worktree remove --force <tmpdir>` after all five
mutations were reverted and hash-verified; a final full offline run inside
the worktree (`20 passed, 6 deselected`) confirmed the restore before
removal. `git status --porcelain` in the shared tree showed no trace of the
worktree afterward.

**P5 adjudication: HELD.** M1 kills exactly the split predicted: the direct
cast test AND the HVO-entry Name-capture test die, while the two
feature-struct-key round-trip tests (which route through
`_ResolveFeatureStrucOwner`'s own internal cast -- a second compensating
layer) survive, along with the C7-raise and slot-ambiguity tests (neither
depends on `__ResolveObject`'s cast for already-typed objects).

## STEP 5 -- comparator delta (two runs, same shell, disposable worktree for "before")

Command (both runs):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
```

BEFORE (worktree checked out at `1d88aa4`, the pre-T7 commit):
```
2 failed, 396 passed, 512 deselected, 8 warnings in 5.67s
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception
```

AFTER (shared tree at `4b746a03`, production + tests committed):
```
2 failed, 416 passed, 518 deselected, 8 warnings in 3.65s
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
FAILED tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception
```

**Delta: +20 passed (exactly the new file's 20 offline tests), +6
deselected (exactly its 6 live tests), failed count UNCHANGED at 2 -- same
two `TestPhase2JoinOrOpen` tests, same messages.** Matches the dispatch's
"EXACTLY 2, not 3, not the old 392" expectation precisely; no other test's
pass/fail status changed.

