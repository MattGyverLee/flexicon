# Live verification -- cycle 10 T6 verification gate

**Project:** Target | **Fixture:** target_sandbox (worktree copy, `git worktree add <tmp> HEAD`, `.fwbackup` copied read-only)
**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project -q`
**run_mode:** live (`tests/live_status.json`, both as-committed and per-mutation runs)
**Date:** 2026-09-07

## Claim under test
T6 (#251) claims MSA feature-struct sync discriminates by `.ClassName`+cast,
holds for base-interface-viewed MSAs (not just factory-fresh handles), and is
behaviourally locked by 21 offline + 6 live tests.

## Mutation results (isolated worktree, MSAOperations.py restored+hash-verified after each)

1. **C2 `__GetMsaObject` cast removed** (return bare `obj` uncast): all 6 live
   tests including `test_hvo_and_guid_entry_paths_capture_feature_keys` stayed
   GREEN. NOT-KILLED -- P0 finding, see LEG 1 in main report.
2. **C6 pop-before-super removed**: `TestMSASyncStatic::test_pop_before_super_source_shape`
   and `TestMSASyncApplyPopBeforeSuper` went RED. PASS-KILLED.
3. **C6 presence-gate -> truthiness**: static AST test
   `test_apply_gates_on_key_presence_not_truthiness` RED; behavioural
   `TestMSASyncApplyPresenceGate` (both cases) stayed GREEN -- NOT-KILLED at
   the behavioural layer (guid value in the fixture is itself truthy, so
   truthiness and presence coincide in that fixture).
4. **C7 `on_unresolved="raise"` -> `"skip"`**: offline
   `TestMSASyncApplyRaisesOnUnresolvedGuid` stayed GREEN (NOT-KILLED --
   `_make_apply_spy` raises unconditionally on `raise_guid`, ignoring the real
   `on_unresolved` value passed in). Live `test_apply_raises_on_unresolved_feature_guid`
   went RED. PASS-KILLED (live only).
5. **R2 both short-circuits removed** (`GetSyncableProperties` +
   `ApplySyncableProperties`): live `test_unclassified_affix_msa_capture_and_apply_do_not_raise`
   stayed GREEN -- NOT-KILLED (the surrounding if/elif dispatch already
   excludes `MoUnclassifiedAffixMsa` structurally; the resolver is never
   reachable for it regardless of the short-circuit). Offline static tests
   (`test_unclassified_affix_discriminated_before_resolver_in_{capture,apply}`)
   went RED. PASS-KILLED (static only).
6. **R1 capture emits flat list instead of C4 dict**:
   `TestMSASyncCapture::test_capture_stem_msa` RED. PASS-KILLED.
7. **LEG 2 dispatch-forced** (`class_name` hard-coded to `"MoStemMsa"` in both
   methods): 9/21 offline tests RED. Offline suite is NOT decorative at the
   dispatch level.
8. **LEG 7 probe** (temporary, deleted before worktree removal): live-created
   `MoDerivAffMsa`, cast `IMoDerivAffMsa(new_msa)`, `hasattr` on
   `FromInflectionClassRA`/`ToInflectionClassRA`/`StratumRA` all `True`.

## Cleanup
All mutations applied/reverted inside a disposable `git worktree add <tmp> HEAD`;
every revert verified via `git hash-object` == `git rev-parse HEAD:<path>`
(`e7e8f791edb089c0b4ae86f10cca4bcd34900194` throughout). Worktree removed with
`git worktree remove --force`. Shared working tree never mutated (`git status`
before/after identical, only pre-existing unrelated entries). Live target_sandbox
is a tempdir copy per pytest fixture, discarded automatically.

## Result
[FINDING] C2's `__GetMsaObject` cast is dead weight -- reported as PASS in the
cycle-9 report but not exercised by any test in the suite. Core discrimination
(`_ResolveFeatureStrucOwner`) is genuinely proven against base-interface-viewed
MSAs by the 3 roundtrip live tests (`sandbox.Object(hvo)` before capture).
