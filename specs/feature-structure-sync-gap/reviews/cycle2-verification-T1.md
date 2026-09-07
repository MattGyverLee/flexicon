# Cycle 2 -- Verification (Gate) T1: lcm_casting._interface_cache feature-structure entries

**GATE: PASS**

## Part 1+2 -- Baseline vs After
Established a pre-change baseline via `git stash push -- flexicon/code/lcm_casting.py`
(only the source file, not the test/contract-snapshot changes), ran both suites, then
`git stash pop` (confirmed via `git status` before the AFTER run).

- Offline (`-m "not requires_live_project"`): BASELINE 1277 passed/0 failed; AFTER 1277
  passed/0 failed. Identical.
- Live (all 7 files): BASELINE 2 failed/82 passed/1 skipped; AFTER 1 failed/83 passed/1
  skipped. The only status change is the new T1 test: FAIL at BASELINE (assertion trips
  on `PartOfSpeech`, `isinstance(project.Object(20918)-cast, IPartOfSpeech)` is `False`
  pre-T1) -> PASS at AFTER. Every other test's status is unchanged, including the
  pre-existing `test_apply_raises_on_type_mismatch_segments_target` failure
  (`AttributeError: 'ICmObject' object has no attribute 'Name'`,
  `NaturalClassOperations.py:1270`), confirmed identical both before and after -- NOT a
  T1 regression. `tests/live_status.json` showed `"run_mode": "live"` on every run
  (BASELINE and AFTER, both offline and live).

## Part 3 -- Evidence
Written to `specs/feature-structure-sync-gap/evidence/live-T1.md` (separate from the
programmer's `live-t1-interface-cache.md`), with exact commands, run_mode, BASELINE/AFTER
counts per suite, and the re-queried pre/post `isinstance` result for the regression test.

## Part 4 -- Anti-trap audit + claim spot-checks

**Claim (i) IPosFeatures absent:** independently confirmed. FieldWorks is genuinely
installed (`HKLM\SOFTWARE\SIL\FieldWorks\9\RootCodeDir` resolves to a real
`FieldWorks.exe`). `tests/contract/snapshots/liblcm_baseline.json`'s `types` dict has no
`IPosFeatures` key and `missing_types` is empty (stale re: this specific name only because
the snapshot predates this check), consistent with the programmer's live introspection
finding. Correctly hardcoded to `None`, no import attempt -- claim upheld.

**Claim (ii) FeaturesOA literal-name only on PhNCFeatures/PhPhoneme:** independently
confirmed against `liblcm_baseline.json`'s `reflected_properties`: `IPhNCFeatures` and
`IPhPhoneme` both have `FeaturesOA`; `IPartOfSpeech` and `IFsComplexFeature` do not
(`DefaultFeaturesOA`/`InherFeatValOA` and `DefaultOA` respectively). Claim upheld.

**Contract snapshot diff:** `expected_contract.json` diff is exactly what's described --
`IFsComplexValue` added in two lists, `total_unique_imports` 255->256, `total_interfaces`
103->104. Agree it is a legitimate T1 consequence, nothing else changed.

**Access-path anti-trap:** confirmed the new test uses a base-interface view, not a
factory-fresh object. Discovery locates only an `.Hvo` via `GetAll()`/`FeatureGetAll()`/an
explicit discovery-only cast; the object actually handed to `cast_to_concrete()` is
`base_obj = project.Object(hvo)` (guaranteed bare `ICmObject`). The assertion
(`concrete = cast_to_concrete(base_obj); assert isinstance(concrete, expected_interface)`)
runs against this re-fetched object, never the discovery-time object. PASS on this check.

**Caller-delta table spot-check:** confirmed zero real callers of `get_common_properties`
(line 869) / `get_concrete_type_properties` (line 945) anywhere in `flexicon/code` or
`tests/` -- the only hits are the functions' own docstring usage examples (lines 889, 966),
not call sites. Table's "zero callers" claim upheld; these are dead utilities, a valid
simplify-candidate finding.

## Blockers
None.

## Recommendation
APPROVE.
