# T6b live evidence -- coverage-honesty follow-up to T6

Test-only change. Production code untouched (confirmed by
`git hash-object` -- see below). File:
`tests/operations/test_issue251_msa_feature_sync.py`.

## Commands run (shared tree, same shell, in order)

```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project -q
```

## Offline comparator delta

| | before (cycle-10 baseline) | after (this cycle) |
|---|---|---|
| passed | 392 | 396 |
| failed | 2 | 2 (same two: `TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`, `::test_depth_restored_on_exception` -- unchanged message, not touched) |
| deselected | 510 | 512 |

+4 passed offline, accounted for by name:
- `TestMSASyncStatic::test_get_msa_object_hasattr_calls_are_allowlisted` (item 4)
- `TestMSASyncStatic::test_resolve_feature_struc_owner_hasattr_calls_are_allowlisted` (item 4)
- `TestMSASyncApplyPresenceGate::test_falsy_but_present_feature_struct_key_still_triggers_apply` (item 3)
- `TestMSASyncApplyPresenceGate::test_falsy_but_present_guid_only_key_still_triggers_apply` (item 3)

(Item 2 renamed an existing test in place -- net zero. Item 1 added 2
new `requires_live_project` tests, accounting for the +2 deselected.)

## Live run

`tests/live_status.json`: `"run_mode": "live"`, `"uncategorized_live_tests": []`.
Full file: 8 passed, 25 deselected (0 failed). Includes the 2 new item-1
tests:
- `TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_stem_msa` -- PASS
- `TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_infl_aff_msa` -- PASS

Pre-state / post-state read back from the LCM for these two (both
re-fetch via the mangled resolver, not the reference held at write
time):
- `sandbox.Object(hvo)` (bare `ICmObject`, pre-cast): `hasattr(..., "MsFeaturesOA")` == False,
  `hasattr(..., "InflFeatsOA")` == False -- confirms the bare fetch genuinely lacks the member.
- `sandbox.MSA._MSAOperations__GetMsaObject(hvo)` and `...(str(msa.Guid))`
  (post-cast): `.ClassName == "MoStemMsa"` / `"MoInflAffMsa"`, and
  `.MsFeaturesOA is None` / `.InflFeatsOA is None` -- direct read succeeds
  (would raise `AttributeError` without the cast) on BOTH the HVO(int)
  and GUID(str) paths, for BOTH C1 rows (MoStemMsa/MsFeaturesOA,
  MoInflAffMsa/InflFeatsOA).

## Item 1 mutation kill (disposable worktree, live)

`git worktree add <tmpdir> HEAD` from commit `c9d2a9a9` (this cycle's
test commit, so the worktree carried the new tests). Copied
`tests/fixtures/Target 2026-07-06 0218.fwbackup` read-only into the
worktree's own `tests/fixtures/`. Pre-mutation hash of
`flexicon/code/Lexicon/MSAOperations.py` inside the worktree:
`e7e8f791edb089c0b4ae86f10cca4bcd34900194` (matches `git ls-tree HEAD`
for the same path in the shared tree).

Mutation: replaced `__GetMsaObject`'s `ClassName`-dispatched cast table
with an unconditional `return obj`.

Result: both new live tests in `TestMSASyncLiveGetMsaObjectCast` FAILED.

Exact failure messages:
```
AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'
  tests\operations\test_issue251_msa_feature_sync.py:1059
  (test_hvo_and_guid_path_cast_to_concrete_stem_msa)

AttributeError: 'ICmObject' object has no attribute 'InflFeatsOA'
  tests\operations\test_issue251_msa_feature_sync.py:1078
  (test_hvo_and_guid_path_cast_to_concrete_infl_aff_msa)
```

Restored the cast, re-ran `git hash-object` inside the worktree:
`e7e8f791edb089c0b4ae86f10cca4bcd34900194` -- identical to pre-mutation.
Full offline suite re-passed in the worktree (25 passed, 8 deselected)
after restore.

## Item 3 mutation kill (same worktree, offline)

Mutation: `__ApplyFeatureStrucProp`'s presence gate
`if key in props or guid_key in props:` changed to a truthiness gate
`if props.get(key) or props.get(guid_key):`.

Result:
- `test_falsy_but_present_feature_struct_key_still_triggers_apply` -- FAILED
  (`assert len(apply_calls) == 1` -> `assert 0 == 1`)
- `test_falsy_but_present_guid_only_key_still_triggers_apply` -- FAILED
  (`assert len(apply_calls) == 1` -> `assert 0 == 1`)
- The two PRE-EXISTING presence-gate tests
  (`test_guid_only_present_still_triggers_apply_with_empty_spec`,
  `test_neither_key_present_never_calls_apply_feature_struc`) stayed
  GREEN under this same mutation -- confirming the cycle-10 finding
  that the pre-existing tests cannot separate presence from
  truthiness because the fixture's Guid value is truthy.

Restored the gate, re-verified `git hash-object` identical to
pre-mutation (same hash as above, since this mutation was applied and
reverted after the item-1 restore was already hash-verified), and
re-ran the full offline suite (25 passed, 8 deselected) to confirm the
restore in place before removing the worktree.

Worktree removed with `git worktree remove --force <tmpdir>` after both
mutations were reverted and hash-verified. Shared tree's
`MSAOperations.py` was never edited: `git diff --stat` empty,
`git hash-object` on the shared-tree copy == `e7e8f791edb089c0b4ae86f10cca4bcd34900194`
throughout.

## Pass/fail

PASS. All five T6b items addressed (see
`specs/feature-structure-sync-gap/reviews/cycle11-programmer-T6b.md`
for the per-item narrative and the narrowness disclosures). Offline
delta +4 passed / 2 unchanged foreign failures / +2 deselected, exactly
accounted for. Live run 8/8 pass, `run_mode: live`, no uncategorized
live tests. Both item-1 and item-3 mutations killed their target
tests and were hash-verified restored in a disposable worktree that
never touched the shared tree's `MSAOperations.py`.
