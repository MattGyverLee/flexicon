# Cycle 6 -- Programmer report, T14a (shipped-suite coverage for MakeFeatStruc's C3 surface)

**Scope:** test-only. No file under `flexicon/code/` was left modified.

## What I built

New file `tests/operations/test_makefeatstruc_c3_live.py`, three
`requires_live_project` tests, all against `target_sandbox` (never the
shared Sena 3), all objects prefixed `TEST_c14a_`:

1. **Nested recursive dict round-trip** -- `{agreement_feat.Hvo:
   {number_feat.Hvo: sg_val.Hvo}}` passed to
   `InflectionFeatures.MakeFeatStruc(specs, owner=<bare MoStemMsa
   object>)`. Re-fetched via a **fresh** `IMoStemMsa(sandbox.Object(stem_hvo))`
   and asserted the top-level `IFsComplexValue.FeatureRA.Name` and the
   nested `IFsFeatStruc`'s `IFsClosedValue.FeatureRA.Name`/`ValueRA.Name`.
   Mirrors the now-deleted cycle-5 gate probe exactly, HVO operands
   included.
2. **`slot=` disambiguation through `MakeFeatStruc` itself** -- one live
   `MoDerivAffMsa`, `MakeFeatStruc(..., slot="From")` then, against a
   second independently-fetched bare object, `slot="To"`. Re-fetched via a
   fresh `IMoDerivAffMsa` cast; asserted `FromMsFeaturesOA.Hvo !=
   ToMsFeaturesOA.Hvo` and each slot's own distinct closed value.
3. **Ambiguous owner, no slot** -- kept (not skipped). See ruling below.

## Ruling on test 3

Read `FEATURE_STRUC_OWNER_TABLE` and `_ResolveFeatureStrucOwner` first, as
instructed. The resolver does **not** silently pick a row when a
two-row `ClassName` (`MoDerivAffMsa`) gets `slot=None` -- it raises
`FP_ParameterError` naming the `ClassName` and the valid slot values
(`BaseOperations.py:1728-1745`, frozen C1 "never guessed"). Since this is
a deliberate raise, not a silent guess, I wrote the test asserting the
raise (message contains `"MoDerivAffMsa"` and `"slot"`) and confirmed via
re-fetch that neither `FromMsFeaturesOA` nor `ToMsFeaturesOA` got a
partial/guessed attach. Nothing was skipped.

## Mutation test result

Backed up `BaseOperations.py`, hash-verified against
`git rev-parse HEAD:...` (`a32d94151f...`). Mutated
`__NormalizeFeatStrucLevel:2575` (`nested = self.__NormalizeFeatStrucLevel(val_raw)`
-> `nested = val_raw`), disabling the nested-dict recursion. Live run
against the mutated code: **1 failed, 2 passed** (down from the clean
baseline's 3 passed) -- `test_nested_dict_spec_round_trips_through_makefeatstruc`
failed with a `TypeError` from the LCM property setter. The other two
tests correctly stayed green (they don't exercise the nested-dict branch;
not this mutation's target). Restored from the scratchpad backup (never
`git checkout`); `git hash-object` == `git rev-parse HEAD:...` exactly;
`git status --porcelain flexicon/code/BaseOperations.py` clean. Clean
re-run after restore: 3 passed, `run_mode: live`.

## Verification summary

- Live: 3/3 passed, `tests/live_status.json` `"run_mode": "live"`.
- Offline pinned subset delta (own before/after, same shell, file
  moved out then restored): `2 failed, 350 passed, 498 deselected` ->
  `2 failed, 350 passed, 501 deselected`. Delta = `+0 passed / +3
  deselected / +0 failed`.
- Determinism: same AFTER command run 3x (2 same shell, 1 fresh shell) --
  all three `2 failed, 350 passed, 501 deselected`.
- No fourth/foreign failure appeared; the two known-foreign
  `test_transaction_rollback.py::TestPhase2JoinOrOpen` failures are
  unchanged and untouched.
- Since every test uses `target_sandbox` (tempdir), the mutation run left
  no residue in the real Target/Sena 3; `restore_target.py --check`
  confirmed Target present/unlocked before and after.

## What I deliberately did not do

- Did not touch `flexicon/code/BaseOperations.py` (or any production
  file) in the committed state -- the mutation was transient and
  restored byte-identical.
- Did not start T14b, T6, or #250 Defect 4.
- Did not touch `tests/conftest.py`, `spec.md`, `STATUS.md`, or
  `.crew-handoff.json`.
- Did not re-diagnose the known-foreign red set.

**Evidence:** `specs/feature-structure-sync-gap/evidence/live-T14a.md`

**Commit:** see the immediately following commit on `main` (this report
is committed alongside it).
