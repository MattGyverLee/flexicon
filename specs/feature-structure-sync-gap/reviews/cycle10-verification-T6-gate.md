# Cycle 10 -- Verification gate: T6 (MSAOperations, #251)

**Verdict: GATE: PASS (with one P0 finding, must be triaged before close)**
**Live run:** yes | **run_mode:** live (all runs)
**Evidence:** specs/feature-structure-sync-gap/evidence/live-cycle10-T6-gate.md
**Project:** Target (target_sandbox, isolated worktree)

All mutations run inside `git worktree add <tmp> HEAD`; shared tree never
touched (`git status` identical before/after); reverts hash-verified against
`e7e8f79...` throughout.

## Verdict table

| Leg | Result |
|---|---|
| 1: base-interface discrimination | ANSWERED -- see below. Core mechanism sound; C2's specific cast is dead code. |
| 2: offline suite falsifiability | Substantially real (9/21 red under dispatch-force); `_MSA_PROP_BY_CLASS_AND_SLOT` confirmed test-only, never in `flexicon/` |
| 3: contract clauses by mutation | 4/6 clean PASS-KILLED; 2 clauses (C7-offline, R2-live) NOT-KILLED at the layer named |
| 4: comparator re-run x2 | Confirmed 392/2/510 both runs, identical foreign pair |
| 5: live re-run as-committed | Confirmed 6 passed, run_mode live, phases correct, uncategorized empty |
| 6: artifact honesty | One overclaim found (report line, not evidence file) |
| 7: ChangeAffixVariant hasattr | Not a trap repeat -- confirmed live |

## LEG 1 -- the central question

**(a) Mechanism:** Two layers. `__GetMsaObject` (:1109-1158) casts by
`.ClassName` via a `{ClassName: interface}.get()` lookup before returning.
Separately, `BaseOperations._ResolveFeatureStrucOwner` (:1717) independently
re-derives `.ClassName` from whatever it's given and re-casts via
`interface_type(unwrapped)` (:1880) -- this is the layer every actual
feature-struct property read/write goes through (`__CaptureFeatureStrucProp`
:1059, `__ApplyFeatureStrucProp` :1095).

**(b)** Yes -- both layers are `.ClassName` + cast, no `hasattr`.

**(c) NO, not cleanly.** Mutating away `__GetMsaObject`'s cast entirely (return
bare `obj`) left **all 6 live tests green**, including
`test_hvo_and_guid_entry_paths_capture_feature_keys` -- the test built
specifically to prove C2. **NOT-KILLED.** Root cause: `_ResolveFeatureStrucOwner`
re-derives and re-casts independently of what `__GetMsaObject` returns (its own
docstring says so: "which casts internally regardless," :1124), so
`__GetMsaObject`'s cast never affects any observable outcome. This is
provably dead code by mutation, not by inspection.

However, the underlying discrimination mechanism the tests actually exercise
(`_ResolveFeatureStrucOwner`) **does** hold for genuine base-interface views:
`test_stem_msa_capture_apply_roundtrip`/`test_infl_aff_msa_...`/
`test_deriv_aff_msa_both_slots_...` all call `sandbox.Object(hvo)` (a bare
`ICmObject` via `ServiceLocator.GetObject`) before `GetSyncableProperties`,
and all three round-trip correctly. Reference paths confirmed genuine
re-fetches (`sandbox.Object(hvo)`, `GetSyncableProperties(hvo_int)`,
`GetSyncableProperties(guid_str)`), never the factory handle held at write
time. The evidence file (`live-T6.md:124-126`) itself candidly admits this:
"reached regardless of whether `__GetMsaObject`'s own eager cast fires
first" -- but the cycle-9 **report** drops that caveat and calls C2
"Live-proven," which is an overclaim (see LEG 6).

## LEG 2/3 mutation detail
See evidence file for the full table. Two named tests are tautological at
the layer claimed: the offline C7 test mocks `_ApplyFeatureStruc` itself
(`_make_apply_spy` raises unconditionally on `raise_guid`, never reads
`on_unresolved`) -- real C7 enforcement is proven only by the live test. The
R2 live no-raise test cannot distinguish presence/absence of either
short-circuit -- the if/elif dispatch structurally excludes
`MoUnclassifiedAffixMsa` regardless, so removing both short-circuits
simultaneously left the live test green; only the two static AST tests
caught it. The zero-hasattr AST test (LEG 3, last bullet) names only
`GetSyncableProperties`/`ApplySyncableProperties`/`__CaptureFeatureStrucProp`/
`__ApplyFeatureStrucProp` -- it does **not** inspect `__GetMsaObject` or
`_ResolveFeatureStrucOwner`, confirmed by reading the test body (:123-149).

## LEG 4/5
Both comparator runs: 392 passed, 2 failed (`TestPhase2JoinOrOpen` pair,
unchanged messages), 510 deselected -- matches report exactly. Live
as-committed: 6 passed, `run_mode: live`, all under
`MSAOperations`/`"modify"`, `uncategorized_live_tests: []`.

## LEG 6 -- overclaim found
Cycle-9 report (`cycle9-programmer-T6.md:35-39`): "**C2**...casts...before
returning...**Live-proven** by `test_hvo_and_guid_entry_paths_capture_feature_keys`
(6/6 live PASS)." This is not supportable per LEG 1(c) above -- the test
proves the HVO/GUID entry path captures correctly, but via
`_ResolveFeatureStrucOwner`, not via `__GetMsaObject`'s cast, which the same
test cannot distinguish from a no-op. CHANGELOG's "closes #251" is NOT an
overclaim -- #251 per spec.md is scoped entirely to MSA, and STATUS.md
confirms #252/#256 are separate T7/T8 tasks.

## LEG 7 -- ChangeAffixVariant hasattr (report only, not fixed)
`deriv_src` at :541 is `concrete_src = IMoDerivAffMsa(msa)` (:526) -- already
concrete-cast, **not** base-interface-viewed, by the time the :545/:550/:555
`hasattr` gates run. Confirmed live: created a real `MoDerivAffMsa` via
`sandbox.MSA.CreateDerivAff`, cast `IMoDerivAffMsa(new_msa)`, and
`hasattr(concrete, "FromInflectionClassRA"/"ToInflectionClassRA"/"StratumRA")`
all returned `True` (matches static `SIL.LCModel` reflection). **Not a trap
repeat** -- these are harmless-but-redundant gates on properties that always
exist on the concrete interface, not silently-dropped data. Probe test
deleted before worktree teardown; never committed.

## Blockers
None requiring `needs_human`. One substantive defect for triage: C2's
`__GetMsaObject` cast is unexercised dead code and the report's "Live-proven"
language for it should be corrected or the redundant cast removed with a
mutation-verified regression test added.

## Mock suite (regression, supplementary)
Command: `python -m pytest -m "not requires_live_project" -q` not separately
re-run in full; LEG 4's scoped comparator (`tests/operations tests/contract`)
serves this purpose and is reported above.

## Recommendation
**FIX ISSUES (non-blocking):** correct the report's C2 claim and either add a
mutation-resistant test for `__GetMsaObject`'s cast or remove it as dead code
now that `_ResolveFeatureStrucOwner` is confirmed to cover the same ground.
All other T6 claims verified live. Do not re-open #251 scope beyond this.
