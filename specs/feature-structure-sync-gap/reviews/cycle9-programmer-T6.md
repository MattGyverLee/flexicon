# Cycle 9 -- Programmer report: T6 (`MSAOperations`, closes #251)

## Commits

- `04b50407` feat(msa): add `GetSyncableProperties`/`ApplySyncableProperties`
  to `MSAOperations.py` (production).
- `941a29eb` chore(msa): `MSAOperations.pyi` stubs for the two new methods.
- `23227b64` test(msa): `tests/operations/test_issue251_msa_feature_sync.py`
  (21 offline + 6 live tests).
- `f7ab3a69` docs(changelog): `[Unreleased] ### Added` entry.
- `e356670e` evidence: T6 live predictions, committed BEFORE the live run.
- `e022a783` evidence: T6 live results (PASS), appended after the run.

## ClassName-vs-hasattr discrimination

Dispatch is entirely `.ClassName`-driven in both `GetSyncableProperties`
and `ApplySyncableProperties`: `MoUnclassifiedAffixMsa` is checked FIRST
(before any resolver call, R2); then `MoStemMsa`/`MoInflAffMsa`/
`MoDerivAffMsa` each delegate to `_ResolveFeatureStrucOwner` (cast via
`IMoStemMsa(obj)` etc., internally, keyed off `ClassName`). Zero
`hasattr` gates on any feature-struct property -- confirmed by
`TestMSASyncStatic::test_zero_hasattr_gates_on_feature_struct_props`,
which asserts `"hasattr" not in` the AST-body (docstring stripped) of
`GetSyncableProperties`, `ApplySyncableProperties`,
`__CaptureFeatureStrucProp`, `__ApplyFeatureStrucProp`. Manual grep of
the whole file shows the only remaining `hasattr` hits are pre-existing
(`ChangeAffixVariant`'s unrelated `FromInflectionClassRA`/
`ToInflectionClassRA`/`StratumRA` checks) or `_obj`-unwrapping idiom,
neither a feature-struct gate.

## Contract/ruling compliance

- **C1**: exactly the 4 in-scope rows (`MsFeaturesOA`, `InflFeatsOA`,
  `From`/`ToMsFeaturesOA`); POS/Allomorph untouched.
- **C2** (`MSAOperations.py:__GetMsaObject`): casts to
  `IMoStemMsa`/`IMoInflAffMsa`/`IMoDerivAffMsa`/`IMoUnclassifiedAffixMsa`
  by `ClassName` before returning, for both HVO (int) and GUID (str)
  entry paths. Live-proven by `test_hvo_and_guid_entry_paths_capture_feature_keys`
  (6/6 live PASS).
- **C6**: `__FEATURE_STRUC_KEYS` filters the 8 keys out of `base_props`
  BEFORE `super().ApplySyncableProperties(...)`; behaviourally locked by
  `TestMSASyncApplyPopBeforeSuper` (spies on the real
  `BaseOperations.ApplySyncableProperties` call and asserts none of the 8
  keys arrived). Presence-gate (`if key in props or guid_key in props`)
  locked by `TestMSASyncApplyPresenceGate` (Guid-only present still
  triggers apply with `spec == {}`; neither key present never calls
  `_ApplyFeatureStruc`).
- **C7**: `on_unresolved="raise"` unconditionally in
  `__ApplyFeatureStrucProp`; `TestMSASyncApplyRaisesOnUnresolvedGuid`
  (offline, mocked) + live `test_apply_raises_on_unresolved_feature_guid`
  both confirm `FP_ParameterError` naming the bogus GUID propagates
  through the public surface.
- **C5**: entirely delegated to the T1-T5 shared helpers; no
  reimplementation.
- **R1**: capture emits the C4 recursive dict via `_GetFeatureStruc`
  (net-new surface, no legacy obligation) -- confirmed by every capture
  test asserting `props["MsFeatures"]["specs"] == {...}` shape, never a
  flat list.
- **R2**: `MoUnclassifiedAffixMsa` short-circuits before the resolver in
  both methods (static order-of-appearance test +
  `_resolver_must_not_be_called` behavioural stub, offline; real
  `MoUnclassifiedAffixMsa` live test, no raise).
- **R3**: one resolver table only --
  `Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE`; MSAOperations
  adds no second copy (the test file's `_MSA_PROP_BY_CLASS_AND_SLOT` is a
  small dict used ONLY to drive a fake mock resolver in offline tests,
  documented as such, never consulted by production code).

## Offline comparator delta

`python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q`,
same shell, before vs. after all commits, run twice post-change for
determinism (identical both times):

- Before: 371 passed, 2 failed (known-foreign `TestPhase2JoinOrOpen`
  pair), 504 deselected.
- After: **392 passed, 2 failed (same pair), 510 deselected.**
- Delta: **+21 passed** (new offline tests), **+6 deselected** (new live
  tests), **0** change in failed/known-foreign identity.

`tests/contract` run in isolation: 22/22 passed -- no contract/snapshot
test went red (R4); `MSAOperations.py`'s import list in
`expected_contract.json` is unaffected since no new `SIL.LCModel` symbol
was imported.

## Live evidence

`specs/feature-structure-sync-gap/evidence/live-T6.md`. Command:
`export FLEXLIBS_REQUIRE_LIVE=1; python -m pytest tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project -q`.
`tests/live_status.json` -> `"run_mode": "live"`, all 6 tests `"status":
"pass"` under `MSAOperations`/`"modify"`, `uncategorized_live_tests: []`.
6/6 PASS: stem round trip, inflAff round trip, derivAff BOTH slots round
trip (proves `slot="From"`/`"To"` reach distinct properties), real
`MoUnclassifiedAffixMsa` no-raise, C7 raise through the public surface,
and the C2 HVO/int + GUID/str entry-path capture. All assertions
re-query a fresh `sandbox.Object(hvo)` post-write, never the reference
held at write time.

## R4 / residue

Nothing went red. One process note: `CHANGELOG.md` was edited and
committed before its lock was acquired (acquired retroactively,
no-conflict) -- process gap, not a substantive issue, named per the
"document the skip reason" norm. An unrelated concurrent session modified
`specs/feature-structure-sync-gap/STATUS.md` and
`specs/250-writingsystem-activation/reviews/cycle8-D4-T6-comment-draft.md`
during this task's live run; left untouched, not committed by me, no
conflict with my locked paths.
