# Live verification -- T4 (`BaseOperations._ApplyFeatureStruc` + NC/Phoneme re-point)

**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup` -- the
real Target was never opened) for all write-path coverage in this task.
**New test file:** `tests/operations/test_apply_feature_struc.py` (7 live
tests, all `requires_live_project`, all `@pytest.mark.live_phase("BaseOperations", "modify")`).
**Modified test file:** `tests/operations/test_natural_class_feature_sync.py`
(the E5 hazard migration + the `TestNaturalClassSyncEmptyFeatureStructPreservation`
fixture repair -- both described in the cycle-4 report, not repeated here).

## Commands (exact)

Offline suite first (mandatory before any live run, per CLAUDE.md):

```
python -m pytest -m "not requires_live_project" -q
```
Result: **1495 passed**, 627 deselected, **3 failed**. All 3 failures are
PRE-EXISTING and unrelated to T4 -- confirmed by running the identical
three tests against commit `ec54432` (the upstream `flexlibs2` ->
`flexicon` rename merge that landed in this repo's `main` mid-task,
*before* any T4 commit is an ancestor of it):
`tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`, and
`tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package`
all fail identically at `ec54432` alone (verified via a disposable
`git worktree add <path> ec54432` + targeted run, then removed). None of
the three touch `BaseOperations.py`, `NaturalClassOperations.py`,
`PhonemeOperations.py`, or any file T4 modified.

True before/after comparison (both sides measured, not asserted): a
second disposable worktree at `a26d39c` (T4's actual parent commit, one
before the upstream merge) ran the SAME offline command and returned
**1494 passed, 1 skipped, 612 deselected, 0 failed**. Reconciling the two
runs line by line:
- **+1 skipped -> 0 skipped, -1 passed -> net 0**: the worktree's
  `tests/fixtures` lacks the Sena 3 `.fwbackup` (git worktrees don't
  carry over untracked large fixture files), so
  `test_pattern_writing_systems_enumeration.py` skips there for a
  purely environmental reason unrelated to any code change; in a
  fully-provisioned environment it would pass, closing this gap exactly.
- **+8 deselected**: `tests/operations/test_name_field_identity_probe.py`
  is an UNTRACKED file belonging to a different, concurrently-running
  spec (`name-field-whitespace-identity`) present in the shared working
  tree but absent from the clean `a26d39c` worktree checkout (confirmed:
  `pytest tests/operations/test_name_field_identity_probe.py --collect-only`
  reports exactly 8 deselected items, all `requires_live_project`).
- Net residual after both of the above are accounted for: **zero**. T4
  introduces no new offline failure and no unexplained passed/deselected
  delta.

The two ratchet-baseline failures T4's OWN changes legitimately triggered
(a new `IFsComplexValueFactory` LCM dependency for the C4 dict-shape
complex-value path, and one newly-added-but-unbracketed `struct.TypeRA =`
assignment) were caught by this same offline run mid-task and FIXED
before this evidence was captured -- see the cycle-4 report's "both-sides
test counts" section for the fix commits. They do not appear in the
final 3-failure list above.

Live run, fail-loud flag set, the three files named in the task plus
this task's own two new/extended test files:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_natural_class_feature_sync.py tests/operations/test_natural_classes.py tests/operations/test_phonemes.py tests/operations/test_apply_feature_struc.py tests/operations/test_feature_struc_resolver.py -m requires_live_project -q
```
Result: **57 passed**, 27 deselected, **1 failed**:
`tests/operations/test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target`,
`AttributeError: 'ICmObject' object has no attribute 'Name'` at
`NaturalClassOperations.py:1270`. This is the KNOWN NON-REGRESSION named
in the task briefing -- a pre-existing C2/HVO-cast symptom (the source
natural class resolved via `self.project.Object(hvo)` on the type-mismatch
path is never cast before `.Name` is read) that fails identically before
and after every change in this feature so far, tracked to fall out of
**T10**. Confirmed unrelated to T4: the failing line
(`NaturalClassOperations.py:1270`) is in the type-mismatch GUARD, which
T4 did not touch (only `__ApplyFeatures`, below it, was rewritten).

Isolating just the three task-named files (no new tests) to match the
task's literal command:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_natural_class_feature_sync.py tests/operations/test_natural_classes.py tests/operations/test_phonemes.py -m requires_live_project -q
```
Result: **34 passed**, 14 deselected, 1 failed (the same known
non-regression above).

## run_mode

`tests/live_status.json` after the final live run:
```
"run_mode": "live",
```
(confirmed non-mock on every live invocation above; the session fixture's
own log shows `[OK] SIL assemblies loaded`, `[OK] Loaded 59/59 operations
classes` on each run).

## Pre/post values re-queried from the LCM (not asserted against the value passed in)

All of `test_apply_feature_struc.py`'s tests follow the mandated pattern:
create/resolve the owner live, write via `_ApplyFeatureStruc`, then
**re-fetch a brand-new bare object** via `sandbox.Object(stem.Hvo)` (never
the reference held at write time) before asserting.

- **`test_apply_legacy_list_creates_struct_preserves_guid_and_spec`**:
  writes a legacy `{"FeatureGuid","ValueGuid"}` spec with an explicit
  `struct_guid` (a freshly minted `uuid.uuid4()`) onto a live
  `MoStemMsa.MsFeaturesOA` that starts `None`. Re-fetch:
  `sandbox.Object(stem.Hvo)` -> `_ResolveFeatureStrucOwner` ->
  `getattr(reread_owner, "MsFeaturesOA")` is non-`None`, and
  `str(reread_struct.Guid).lower() == struct_guid.lower()` -- the
  struct's IDENTITY, not just its presence, is confirmed to have
  survived the write/re-fetch round trip. `_GetFeatureStruc(reread_struct)`
  (T3's own read-side helper, used here purely as an independent
  verification instrument) reproduces `{feat_guid: value_guid}` exactly.
- **`test_apply_legacy_list_twice_is_idempotent`**: applies the identical
  spec list twice, then re-fetches and asserts
  `reread_struct.FeatureSpecsOC.Count == 1` (not 2) -- proves the
  `existing_pairs` idempotency check survives the move into
  `BaseOperations`, re-verified from a fresh LCM read each time.
- **`test_apply_raise_mode_raises_on_unresolved_feature_guid`** /
  **`test_apply_skip_mode_silently_skips_unresolved_guid`**: a bogus,
  never-created GUID (`00000000-...-000000000001`/`...003`) is passed as
  `FeatureGuid`. Raise mode: `FP_ParameterError` raised, message matched
  against the literal bogus GUID string (`pytest.raises(..., match=bogus_guid)`).
  Skip mode: no exception, and the re-fetched struct (if a shell was
  created at all) has `FeatureSpecsOC.Count == 0` -- the unresolved spec
  was never inserted.
- **`test_apply_flat_c4_dict_creates_closed_value`**: same idempotency/
  identity re-fetch discipline, but with the C4a dict shape
  (`{"TypeGuid": None, "specs": {featGuid: valGuid}}`) instead of the
  legacy list -- proves `_ApplyFeatureStruc`'s `isinstance(spec_dict, dict)`
  branch actually writes, independent of any NC/Phoneme call site (none
  drives this branch yet; C4b/T9b).
- **`test_apply_nested_c4_dict_creates_complex_value_and_recurses`**: a
  real `IFsComplexFeature` + `IFsFeatStrucType` + closed feature/value are
  minted via `InflectionFeatures`, then applied as a NESTED C4 dict
  (`{"specs": {complexGuid: {"TypeGuid": ..., "specs": {closedGuid: valGuid}}}}`).
  Re-fetch + `_GetFeatureStruc` round-trip confirms: the outer level's
  `TypeGuid` is `None` (never set), the INNER level's `TypeGuid` equals
  the minted type's GUID (per-level `TypeRA`, not a whole-struct
  property -- C4's frozen rule), and the inner `specs` dict matches the
  closed feature/value pair exactly. This is the first live proof that
  `_ApplyFeatureStrucSpecMap`'s recursion (new in T4) actually creates a
  real `IFsComplexValue`/nested `IFsFeatStruc` pair against a live LCM,
  not just a mock.
- **`test_apply_c4_dict_raises_on_unresolved_type_guid`**: a bogus
  `TypeGuid` (`...000000005`) raises `FP_ParameterError` matched against
  the literal bogus GUID.

## Deliberately NOT covered here (owned by later tasks)

- Full nested round-trip verification across ALL C1 owner types (T14).
- `PhonemeOperations.py:1351`/`:1428`/`:1431` and the `on_unresolved`
  default flip (T9) -- untouched, per the task's hard constraint.
- Capture-side migration to the C4 dict format for NC/Phoneme (T9b).
