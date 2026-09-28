# Live verification -- issue #280 (LexiconSetComplexFormType hasattr gate)

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue280_complex_form_type_cast_live.py -m requires_live_project -q
```

Run against `target_sandbox` (fresh tempdir copy of the Target `.fwbackup`),
not the in-place `target_project`, per the task's concurrency note.

## Result

```
....                                                                     [100%]
[OK] Wrote D:\Github\_Projects\_LEX\flexicon\tests\test_results.json (4 tests recorded)

4 passed in 7.61s
```

`tests/live_status.json` after the run:

```json
"run_mode": "live",
"run_timestamp": "2026-09-10T19:32:34Z"
```

`run_mode: "live"` confirms this was not a mock-mode pass.

## Pre-state / post-state, read back from the LCM

### `LexiconSetComplexFormType` -- `test_set_complex_form_type_persists_on_hvo_resolved_ref`

1. Created `TEST_sun280` (component) and `TEST_sunflower280` (complex form)
   via `target_sandbox.LexEntry.Create`.
2. `LexiconAddComplexForm(complex_form, [component], None)` created an
   `ILexEntryRef` with `RefType = krtComplexForm` and no complex form
   type set. Its `Hvo` was captured.
3. **Precondition check**: re-fetched the entry ref via
   `target_sandbox.project.ServiceLocator.GetObject(hvo)` (no cast) and
   asserted `not hasattr(base_typed_ref, "ComplexEntryTypesRS")` --
   this passed, confirming the object genuinely arrives base-typed
   (`ICmObject`) through this path, which is the exact precondition the
   pre-fix bug depended on.
4. **Pre-state** (fresh `ServiceLocator.GetObject(hvo)` + `cast_to_concrete`,
   then `[t.Hvo for t in ref.ComplexEntryTypesRS]`): `[]`.
5. Called `target_sandbox.LexiconSetComplexFormType(base_typed_ref, cf_type)`
   with the **base-typed** `entry_ref` from step 3 -- exactly the shape
   that used to make the method a silent no-op.
6. **Post-state** (same fresh re-read pattern): `[cf_type.Hvo]` --
   the complex form type was written and is visible on a completely
   independent re-fetch of the object, proving the write reached the
   LCM rather than merely mutating the caller's in-memory reference.

Before the fix (`hasattr` gate with no cast, no `else`), step 5 would
have executed silently with **no exception and no write**, and step 6
would have read back `[]` -- the issue's documented silent no-op.

### `LexiconSetComplexFormType` -- `test_set_complex_form_type_raises_on_wrong_object_type`

Passed a genuine `ILexEntry` (not a `LexEntryRef`) as `entry_ref`.
Asserted `pytest.raises(FP_ParameterError)`. Passed -- confirms the
guard is now loud instead of a silent success.

### `LexiconGetComplexFormType` -- `test_get_complex_form_type_reads_on_hvo_resolved_ref`

Same construction, but `cf_type` passed directly into
`LexiconAddComplexForm` so the ref already carries a complex form type.
Re-fetched base-typed (`not hasattr(..., "ComplexEntryTypesRS")`
asserted True) and called `LexiconGetComplexFormType(base_typed_ref)`;
result's `.Hvo` matched `cf_type.Hvo`. Repeated with a second,
independent `ServiceLocator.GetObject(ref_hvo)` fetch to rule out any
state cached on the first reference. Both reads matched.

Before the fix this would have silently returned `None` for a
base-typed `entry_ref`, indistinguishable from "this ref genuinely has
no complex form type."

### `LexiconGetComplexFormType` -- `test_get_complex_form_type_raises_on_wrong_object_type`

Passed a genuine `ILexEntry`. Asserted `pytest.raises(FP_ParameterError)`.
Passed.

## Blocking issue found and fixed during verification

The originally-planned fix (`cast_to_concrete(entry_ref)` +
`hasattr`-based raise) did not work on first live run:
`cast_to_concrete` returned the object **unchanged** for `ClassName ==
"LexEntryRef"` because `"LexEntryRef"` was not registered in
`lcm_casting.py`'s `_interface_cache` at all -- `ILexEntryRef` was never
imported or mapped. `cast_to_concrete` is total (returns the original
object for an unrecognised `ClassName`), so this failure was itself
silent: no exception, just a `cast_to_concrete` call that did nothing,
reproducing the exact symptom this fix was meant to eliminate one layer
down.

Fixed by registering `"LexEntryRef": ILexEntryRef` in
`flexicon/code/lcm_casting.py` (import block + registration block +
docstring), guarded with the same `try/except ImportError` pattern used
for every other optional interface in that module. `ILexEntryRef` is
confirmed present in `tests/contract/snapshots/expected_contract.json`.
Rerunning the live suite after this addition produced the 4/4 pass
above.

## Pass/fail

**PASS** -- live, `run_mode: "live"`, 4/4 tests green, pre-state and
post-state both read back from independent LCM re-fetches.
