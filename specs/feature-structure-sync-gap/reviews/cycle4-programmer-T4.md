# Cycle 4 -- Programmer report: T4

`BaseOperations._ApplyFeatureStruc` (+ `_ApplyFeatureStrucSpecMap` recursion
helper, + three `_CastFs*` test-seam methods) extracted; NC re-pointed with
`on_unresolved="raise"`, Phoneme re-pointed with `on_unresolved="skip"`. Both
private `__ResolveByGuid` twins removed (de-duplicated into T3's
`_ResolveFsByGuid`). Phoneme's dead `fill_gaps` parameter removed at the
call-through. T5 and all later tasks were NOT started.

## (a) Where the code lives

- `flexicon/code/BaseOperations.py`: new `_CastFsFeatStruc`,
  `_CastFsClosedValue`, `_CastFsComplexValue` (tiny cast-wrapper methods,
  see (d) below for why they exist), `_ApplyFeatureStruc` (C5/C6/C7 + C4a),
  `_ApplyFeatureStrucSpecMap` (private recursion helper for the C4 dict
  shape, not part of the C5 frozen surface), inserted between
  `_ResolveFsByGuid` (T3) and `_RejectLegacyKwargs`.
- `flexicon/code/Grammar/NaturalClassOperations.py`: `__ApplyFeatures` is now
  an 11-line thin call-through; `__ResolveByGuid` removed entirely (its only
  callers were inside the removed `__ApplyFeatures` body).
- `flexicon/code/Grammar/PhonemeOperations.py`: `__ApplyFeatures` is now a
  thin call-through (signature dropped `fill_gaps`, its one caller updated);
  `__ResolveByGuid` removed entirely.
- `tests/contract/snapshots/expected_contract.json`: minimal, surgical
  2-line-plus-summary addition of `IFsComplexValueFactory` (the one
  genuinely NEW LCM type dependency T4 introduces, for the C4 dict shape's
  complex-value creation). Deliberately NOT regenerated wholesale -- a full
  `python -m tests.contract.extract_lcm_contract` run pulled in ~50 lines of
  unrelated drift accumulated since the last regen (stale `code/transaction.py`
  / `code/undoable_operation.py` entries, other files' local imports never
  captured), which would have laundered unrelated changes into this commit.
  Reverted that wholesale regen; added only the one new name by hand.
- `flexicon/code/BaseOperations.py`: one previously-unbracketed
  `struct.TypeRA = type_obj` assignment (in the new
  `_ApplyFeatureStrucSpecMap`) wrapped in
  `with self._TransactionCM("Set feature structure type"):` per the
  `write-path-transactions` ratchet (`test_no_new_unbracketed_mutations`
  caught this mid-task; fixed before finalizing, see (e)).
- `tests/operations/test_natural_class_feature_sync.py`: the E5 hazard
  migration (see (b)) + a fixture repair in
  `TestNaturalClassSyncEmptyFeatureStructPreservation` (see (c)) -- both
  necessary for the file to pass at all after the move, not optional
  cleanup.
- `tests/operations/test_apply_feature_struc.py`: NEW file, 7 live tests
  directly exercising `_ApplyFeatureStruc`/`_ApplyFeatureStrucSpecMap`
  (legacy list + C4 dict shapes, both flat and nested) against
  `target_sandbox`, independent of any NC/Phoneme call site.

Commits: `4aca74a` (production + contract/ratchet fixes + the migrated test
file), `61e0f878` (the new live test file). Both on `main` directly (no PR
branch -- this repo's established norm for this feature, matching T1-T3).

## (b) The E5 hazard -- assertion-by-assertion migration

`tests/operations/test_natural_class_feature_sync.py:77-160` (pre-T4 line
numbers) held `inspect.getsource` shape assertions against
`_NaturalClassOperations__ApplyFeatures`. All were migrated 1:1 onto
`BaseOperations._ApplyFeatureStruc` via a new `_base_method_source(name)`
helper (mirrors the existing `_method_source` helper, reading from
`BaseOperations.__dict__` instead of `NaturalClassOperations.__dict__`).
None were deleted or weakened.

| # | Original assertion (pre-T4 line) | What it pinned | New location | New form | Why it pins the same property |
|---|---|---|---|---|---|
| 1 | `"raise FP_ParameterError" in src` (~126) | The method raises `FP_ParameterError` somewhere. | `_ApplyFeatureStruc` | Identical string check, `src = _base_method_source("_ApplyFeatureStruc")`. | Literal substring; `_ApplyFeatureStruc` still contains multiple `raise FP_ParameterError(...)` call sites in its `on_unresolved == "raise"` branch. |
| 2 | `"feat_obj is None" in src and "raise" in src` (~130) | A `None` `feat_obj` (unresolved `FeatureGuid`) is checked and raised on, not silently skipped. | `_ApplyFeatureStruc` | Same two substring checks, unchanged variable name `feat_obj`. | The variable name `feat_obj` was kept verbatim in the migration (only `nc_name` was renamed, to `label` -- see #5); `if feat_obj is None: raise FP_ParameterError(...)` is textually present in the `on_unresolved == "raise"` branch. |
| 3 | `"val_obj is None" in src` (~134) | A `None` `val_obj` (unresolved `ValueGuid`) is checked and raised on. | `_ApplyFeatureStruc` | Same substring check, unchanged variable name `val_obj`. | Same reasoning as #2; `if val_obj is None: raise FP_ParameterError(...)` present in the raise branch. |
| 4 | `unresolved_section = src[src.index("feat_obj = self.__ResolveByGuid"):]`; `assert "continue" not in unresolved_section.split("val_obj = self.__ResolveByGuid")[0]` (~144-146) | Between resolving `feat_obj` and resolving `val_obj` (in the branch NC actually takes), there is no silent `continue` -- an unresolved FeatureGuid must raise, not fall through. | `_ApplyFeatureStruc` | `self.__ResolveByGuid` -> `self._ResolveFsByGuid` (T3's shared resolver, which T4 was explicitly tasked to de-duplicate onto). Added a clarifying comment that `_ApplyFeatureStruc` now has TWO `feat_obj = self._ResolveFsByGuid(...)` call sites (raise-mode branch, then skip-mode branch, since one method now serves both NC and Phoneme) -- `src.index(...)` finds the FIRST (the `on_unresolved == "raise"` branch, textually first and the one NC's `on_unresolved="raise"` call-through actually exercises), so the slice-and-check still isolates exactly the raise-mode resolution pair with no continue between them. | The property -- "the raise-mode unresolved-FeatureGuid branch never silently continues" -- is unchanged. The literal method name changed only because T4's OWN mandate was to eliminate the duplicate `__ResolveByGuid` methods in favour of `_ResolveFsByGuid`; keeping the OLD literal would have meant NOT doing that de-duplication, which the task explicitly required. |
| 5 | `"{feat_guid}" in src or "feat_guid}" in src` AND `"{nc_name}" in src or "nc_name}" in src` (~151, 155) | The raised exception message names both the offending GUID and the failing natural class. | `_ApplyFeatureStruc` | `feat_guid` kept verbatim; `nc_name` -> `label` (the new C5-frozen parameter name: `assert "{label}" in src or "label}" in src`). | `label` is the generalized replacement for `nc_name` mandated by C5's frozen signature (`_ApplyFeatureStruc(owner, prop_name, spec_dict, struct_guid=None, on_unresolved="raise", label=None)`) -- a single shared method serving 8+ C1 owner types cannot hard-code "natural class" in its error strings. NC's call-through passes `label=f"natural class '{nc_name}'"`, so the RENDERED message text for NC is byte-identical to before (`"...natural class 'X' Features entry is not a dict: ..."` etc.) -- verified by inspection of the f-string construction, not just by assertion. The property being pinned (message names the GUID and the failing item) is unchanged; only the variable name for "the failing item" is generalized, exactly as C5 requires. |

All five were counted independently in the task briefing as "five
`inspect.getsource` shape assertions" (some grouped two per `assert`
statement, as shown above); all five are accounted for in the table.

**Not touched (and correctly so):** `test_no_hasattr_gate_on_subtype_only_members`
(~line 231+ pre-T4) also calls `_method_source("_NaturalClassOperations__ApplyFeatures")`
for its `apply_features_src` variable, checking for absence of
`hasattr(nc, "FeaturesOA"/"SegmentsRC")` gate idioms. This assertion was
LEFT pointed at NC's own (now-thin) call-through deliberately: the
call-through trivially satisfies it (it contains no such gate at all --
it is 11 lines of variable setup and one delegating call), so the
assertion is not weakened, and re-pointing it at `_ApplyFeatureStruc` would
have been redundant (that method never had such a gate either -- it reads
`getattr(owner, prop_name)` generically, never `hasattr`). This is NOT one
of the five hazard assertions named in the task; it was reviewed and left
alone as out of scope for the minimal migration.

## (c) The second hazard found during implementation (not named in the task briefing, found empirically)

`TestNaturalClassSyncEmptyFeatureStructPreservation` (behavioural, not
source-text, coverage in the same test file) monkeypatches
`NaturalClassOperations`'s own MODULE-LEVEL `IFsFeatStruc`/`IFsClosedValue`
names to identity functions so its `_Fake*` Python stand-ins can flow
through the algorithm without a real pythonnet cast. Moving the actual
struct-casting code into `BaseOperations._ApplyFeatureStruc` (which does
its own fresh `from SIL.LCModel import ...` local imports, per the existing
`_GetFeatureStruc`/T3 precedent) made that monkeypatch a no-op for the
moved code, and the real `IFsFeatStruc(fake_object)` call raised
`TypeError: object does not implement IFsFeatStruc` -- confirmed empirically
by running the suite before attempting any fixture fix.

The first fix attempted -- patching `SIL.LCModel`'s own module attributes
directly (`monkeypatch.setattr(lcm, "IFsFeatStruc", ...)`) -- ALSO failed,
with `AttributeError: type does not support setting attributes`: `SIL.LCModel`
is a pythonnet CLR namespace, not a regular Python module, and rejects
`setattr` outright. This ruled out the "patch the real module" approach
entirely, and also rules it out as an option for any FUTURE fake-object test
of LCM-casting code living directly in `BaseOperations.py` (recorded here so
the next task doesn't rediscover this by trial and error).

**Fix:** added three tiny one-line `BaseOperations` methods --
`_CastFsFeatStruc`, `_CastFsClosedValue`, `_CastFsComplexValue` -- each
wrapping exactly one `IFs*(obj)` cast, called from `_ApplyFeatureStruc`/
`_ApplyFeatureStrucSpecMap` instead of the cast being inlined. `BaseOperations`
IS a plain Python class (unlike the CLR namespace), so `monkeypatch.setattr(
BaseOperations, "_CastFsFeatStruc", lambda self, x: x)` works exactly like the
PRE-EXISTING `_TransactionCM`/`_CreateWithGuid` monkeypatches already used by
this same fixture -- same technique, extended to cover the newly-shared cast
points. Updated the fixture accordingly; all 4 previously-failing tests in
this class now pass (verified: 14/14 in the file, up from 10/14 immediately
after the raw move, before this fix).

This is a genuine, necessary testability seam, not scope creep: without it,
"behaviour-preserving" for NC's OWN pre-existing behavioural test coverage
would have been silently broken by the refactor. Production callers are
unaffected -- `self._CastFsFeatStruc(obj)` performs exactly the
`IFsFeatStruc(obj)` cast the inline call used to.

## (d) C4a dual wire-shape normalisation approach

`_ApplyFeatureStruc` detects the shape via `isinstance(spec_dict, dict)`:

- **List (or `None`, treated as `[]`) -> legacy branch.** Applied with a
  per-item algorithm that is a PARAMETERIZED (not rewritten) copy of the
  original NC/Phoneme loop: same idempotency set, same malformed-item
  handling (raise in `on_unresolved="raise"` mode, `continue` in `"skip"`
  mode -- this mirrors exactly how NC always raised and Phoneme always
  skipped for malformed entries pre-T4), same lazy `val_obj` resolution in
  raise-mode (feat resolved and checked BEFORE val is even resolved,
  matching NC's original code exactly) vs. resolve-both-then-check in
  skip-mode (matching Phoneme's original code exactly). Items are applied
  ONE AT A TIME in original list order -- a `"raise"`-mode failure partway
  through leaves every already-processed prior item's mutation committed,
  identical to the pre-T4 behaviour. This was a deliberate choice NOT to
  "normalise legacy -> C4 dict as a literal preprocessing pass": a dict
  can't represent "malformed entry N of an otherwise-valid list" in a way
  that preserves per-item ordering/partial-application semantics, and
  building that preprocessing step would have risked a real (if
  edge-case) behavioural delta on the malformed-entry path that
  NC's/Phoneme's own tests don't exercise but which the "zero runtime
  delta" mandate still covers.
- **Dict -> C4 branch.** Delegates to the new `_ApplyFeatureStrucSpecMap`
  recursion helper, which reads `spec.get("TypeGuid")` (applied to
  `struct.TypeRA`, per-level, transactionally) and walks `spec.get("specs")`:
  a scalar value is a closed feature/value pair (mirrors the legacy
  branch's closed-value creation); a dict value is a nested complex
  feature, creating (or reusing, for idempotency) an `IFsComplexValue`
  whose `ValueOA` is populated by recursing. Idempotency here is tracked
  via `existing_closed`/`existing_complex` dicts keyed by lower-cased
  feature GUID, read once per level before that level's loop -- the C4
  analogue of the legacy branch's `existing_pairs` set.

Neither NC nor Phoneme drives the dict branch today (both keep emitting
the legacy list; C4b/T9b). It is exercised end-to-end, including one
level of nesting, by the new `tests/operations/test_apply_feature_struc.py`
(live, against `target_sandbox`) -- see the evidence file.

## (e) Both-sides test counts

**Offline** (`python -m pytest -m "not requires_live_project" -q`):

| | Passed | Failed | Skipped | Deselected |
|---|---|---|---|---|
| Before T4 (`a26d39c`, T4's actual parent, measured via disposable `git worktree`) | 1494 | 0 | 1 | 612 |
| After T4 (final state, includes the new live test file) | 1495 | 0 | 0 | 627 |

The `+1 passed / -1 skipped` and `+15 deselected` deltas are FULLY
reconciled in the evidence file (`evidence/live-T4.md`) as environmental
(missing Sena 3 fixture in the disposable worktree) and concurrent-work
artifacts (an untracked file from a different, simultaneously-running
spec, plus this task's own 7 new live tests correctly deselected by the
offline marker filter) -- not a T4 regression. Net unexplained residual:
zero.

**Mid-task, self-caught regressions (fixed before finalizing, not present
in the final state):** the raw move initially introduced 2 NEW offline
ratchet-test failures (`test_no_new_type_dependencies` -- the new
`IFsComplexValueFactory` LCM dependency; `test_no_new_unbracketed_mutations`
-- one unbracketed `TypeRA` assignment) and left 4 of
`TestNaturalClassSyncEmptyFeatureStructPreservation`'s 6 tests failing (the
monkeypatch hazard in (c)). All 6 are fixed in the final state (see (b)/(c)/
above).

**Live** (`$env:FLEXLIBS_REQUIRE_LIVE = "1"`, `tests/live_status.json` ->
`"run_mode": "live"` confirmed on every run):

| Command | Passed | Failed | Deselected |
|---|---|---|---|
| The three task-named files (`test_natural_class_feature_sync.py test_natural_classes.py test_phonemes.py`) | 34 | 1 (known non-regression, see below) | 14 |
| + this task's own two test files (`test_apply_feature_struc.py`, `test_feature_struc_resolver.py`) | 57 | 1 (same) | 27 |

The one live failure,
`test_apply_raises_on_type_mismatch_segments_target`
(`AttributeError: 'ICmObject' object has no attribute 'Name'` at
`NaturalClassOperations.py:1270`), is the KNOWN NON-REGRESSION named in the
task briefing. Confirmed unrelated to T4: line 1270 is inside the
TYPE-MISMATCH GUARD (`if nc.ClassName != "PhNCFeatures": name_text =
ITsString(nc.Name...)`), which sits ABOVE `__ApplyFeatures` in
`ApplySyncableProperties` and was not touched by this task -- only
`__ApplyFeatures` itself (below the guard) was rewritten. Full detail in
`evidence/live-T4.md`.

## What was deliberately NOT touched

- `PhonemeOperations.py:1351` (HVO-path cast), `:1428` (truthiness gate at
  the `ApplySyncableProperties` call site), `:1431` -- wait, per the
  task's own line numbering these are the three sites explicitly reserved
  for **T9**; none were touched. The ONLY change to `PhonemeOperations.py`'s
  `ApplySyncableProperties` was the one-argument change to the
  `__ApplyFeatures` call (`self.__ApplyFeatures(phoneme, features,
  fill_gaps)` -> `self.__ApplyFeatures(phoneme, features)`), required
  because T4 also removed the dead `fill_gaps` parameter from
  `__ApplyFeatures` itself (explicitly assigned to T4 in the briefing).
  The `if features:` truthiness GATE guarding that call is untouched.
- Phoneme's struct-GUID preservation gap: `_ApplyFeatureStruc` ALWAYS
  accepts and would honour a `struct_guid`, but Phoneme's call-through
  passes `struct_guid=None` because `PhonemeOperations.ApplySyncableProperties`
  has never extracted `props.get("FeaturesGuid")` in the first place --
  there is no GUID available to thread through yet. This is explicitly
  T9's job (together with `:1351`/`:1431`, "these three land together or
  none is testable" per the task list). Not fixed here, and the
  call-through's docstring says so explicitly.
- `test_no_hasattr_gate_on_subtype_only_members`'s `apply_features_src`
  variable -- left pointed at NC's own thin call-through (see (b), last
  paragraph).
- The whole-file regeneration of `expected_contract.json` -- reverted in
  favour of a minimal, 2-line-plus-summary hand edit (see (a)) to avoid
  laundering unrelated drift into this commit.
- T5 (generalized `MakeFeatStruc`) and every later task -- not started,
  per the explicit instruction.

## Files changed

- `flexicon/code/BaseOperations.py`
- `flexicon/code/Grammar/NaturalClassOperations.py`
- `flexicon/code/Grammar/PhonemeOperations.py`
- `tests/contract/snapshots/expected_contract.json`
- `tests/operations/test_natural_class_feature_sync.py`
- `tests/operations/test_apply_feature_struc.py` (new)
- `specs/feature-structure-sync-gap/evidence/live-T4.md` (new)
- `specs/feature-structure-sync-gap/reviews/cycle4-programmer-T4.md` (this file)

Commits: `4aca74a`, `61e0f878`, both directly on `main`.
