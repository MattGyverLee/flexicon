# Cycle 2 -- Programmer implementation report, issue #254

## What changed

`flexicon/code/TextsWords/WfiMorphBundleOperations.py`:
- Imports: added `import logging` + `logger = logging.getLogger(__name__)`
  (L15, L33) and `IMoForm` to the `SIL.LCModel` import block (L21).
- `GetMorphType` (now L790-857): repaired in place. Returns
  `bundle.MorphRA.MorphTypeRA`. `MorphRA is None` -> `logger.warning`
  naming `bundle.Hvo` (L843-847), return `None`. `MorphRA` set but
  `MorphTypeRA is None` -> silent `None` (L857). Used bare
  `morph.MorphTypeRA` per C1's preference, with a comment (L850-856)
  citing the 4.5.1 precedent and instructing lex-verification to switch
  to an explicit `IMoForm(morph).MorphTypeRA` cast if bare access proves
  hidden live.
- `SetMorphType` (now L860-911): retired. Raises `FP_ParameterError`
  unconditionally as the *first* statement (L902-911) -- no
  `_EnsureWriteEnabled()`, no `_ValidateParam`, no `_TransactionCM`, no
  `__GetMorphTypeObject` call. Signature keeps `morph_type_or_hvo`
  (documented as ignored). Message names both replacements verbatim per
  spec.md C2.
- `GetMorph` (new, L914-958): returns `bundle.MorphRA` (today's old
  `GetMorphType` behavior), `None` silently, no warning.
- `SetMorph` (new, L961-1017): resolves outside the transaction via new
  `__GetMorphObject` (L1449-1467, does NOT reuse `__GetMorphTypeObject`),
  then guards `isinstance(morph, IMoForm)` before entering
  `_TransactionCM`, raising `FP_ParameterError` naming the received
  `ClassName` (L1009-1014) if not. Accepts `None` to clear.
- C5 docstrings: rewrote `GetMorphType`'s Example to use
  `Name.BestAnalysisAlternative.Text` (matches live-probe finding that
  `get_String` returns empty), documented the `MorphRA is None` warning,
  `See Also -> GetMorph`. Deleted `SetMorphType`'s entire old Example
  block (the `MorphTypesOA.PossibilitiesOS` pull + `"suffix" in
  str(mt).lower()` filter + both assignment lines); replaced `Args`/
  `Notes`/`See Also` to state the retirement and point at
  `project.Allomorphs.SetMorphType` / `SetMorph`.

`CHANGELOG.md`: added a `### Changed` entry under `[Unreleased]` (no
version cut, no version string bumped) covering the `GetMorphType`
return-type flip (BREAKING, behavioural), `SetMorphType`'s retirement,
and the new `GetMorph`/`SetMorph` pair, following the #232-era prose
style.

`tests/operations/test_wfi_morph_bundle.py`: added
`TestWfiMorphBundleMorphTypeContract` (5 new tests, all offline, all
green): method-presence check; `SetMorphType` raises
`FP_ParameterError` unconditionally for `object()`/`None`/`int` args,
message names both replacements; `SetMorphType` raises before touching
*any* attribute on `self` (bare mock proves no `_EnsureWriteEnabled`/
resolver call happens first); `SetMorph` rejects a non-`IMoForm` object
naming its `ClassName`; `SetMorph(bundle, None)` clears `MorphRA`. Ran
314/314 non-live tests green (`pytest tests/operations/ -m "not
requires_live_project"`).

## Ambiguities and choices made

- **Descriptor gotcha discovered while writing tests, not in scope but
  worth flagging**: `OperationsMethod.__get__` at *class* level
  (`Class.Method(x, ...)`) treats `x` as `project` and constructs a
  fresh instance -- it does NOT let a caller substitute a fake `self`.
  The existing `test_set_gloss_raises_unconditionally`/
  `test_get_gloss_returns_empty_for_unlinked_bundle` precedents worked
  around this only because those methods never touch `self.project`
  before returning/raising. `SetMorph` does (`_EnsureWriteEnabled`,
  `_TransactionCM`), so I switched to real instantiation
  (`WfiMorphBundleOperations(_StubProject())` then `ops.SetMorph(...)`)
  plus class-level monkeypatching of `_TransactionCM` and the two
  mangled resolvers, restored in `finally`. Not a #254 bug -- just noting
  it cost debugging time and could bite future tests on write methods.
- **`__GetMorphTypeObject` (L1430-1442)**: spec said remove its *call*
  from `SetMorphType`, not delete the method. It is now unused (no
  remaining callers) -- left in place since deletion wasn't asked for;
  flagged in its docstring and in `__GetMorphObject`'s docstring as
  currently uncalled.
- Docstring sweep (C5, last bullet): grepped for the `"suffix"/"prefix"
  in str(mt).lower()` idiom and the `MorphTypesOA.PossibilitiesOS ->
  bundle-assignment` pattern codebase-wide. Found only one other hit:
  `AllomorphOperations.SetMorphType`'s docstring Example (L923-931,
  `"prefix" in str(mt).lower()`), which assigns into
  `allomorph.MorphTypeRA` -- a field genuinely typed `IMoMorphType`, so
  the *assignment* is correct (matches spec's "AllomorphOperations:871
  already correct, do not fix"); only the fragile substring-match idiom
  is shared, not the bundle-assignment bug shape. `LexEntryOperations.py`
  L1516/1593 pull from `MorphTypesOA` too but assign into
  `entry.LexemeFormOA.MorphTypeRA` (also correctly typed) and use
  `morph_types[0]`, not the substring idiom. Left both alone per the
  explicit "AllomorphOperations:871 and LexEntryOperations:1443 already
  correct, do not fix" instruction -- reporting per C5, not fixing.

## Probe-test assertions

`test_issue254_morphra_probe.py` needed **no assertion changes**. Its
only `ops.`-level calls are `ops.SetMorphType(target_bundle,
bogus_morph_type)` (L138) and `ops.GetMorphType(...)` inside an `if
raised is None:` branch (L144-180) that was already dead before this fix
-- the live probe (evidence file) already found `SetMorphType` crashes
with `TypeError` at the pythonnet boundary on every real call, so
`raised` was never `None` even under the old code. Post-fix, `raised`
becomes an `FP_ParameterError` string instead of a `TypeError` string,
but the test only prints it, never asserts on its type/text, so no
`assert` flips either way. Left the file untouched.

## Left for lex-verification

- Whether bare `bundle.MorphRA.MorphTypeRA` resolves under pythonnet, or
  needs `IMoForm(bundle.MorphRA).MorphTypeRA`. Comment in `GetMorphType`
  (L850-856) documents both paths and the CHANGELOG [4.5.1] precedent;
  shipped with the bare form per spec's stated preference, pending live
  confirmation against `target_sandbox`/`sena3_sandbox`.
- Live confirmation of the `GetMorphType` warning firing correctly for a
  bundle with `MorphRA is None`, and of `SetMorph`'s `IMoForm` guard
  against a real `IMoMorphType` object (only a plain-Python fake was
  exercisable offline).
- `docs/API_ISSUES_CATEGORIZED.md` was not touched -- no existing entry
  referenced this issue/file, and it wasn't listed among the required
  artifacts in spec.md or the dispatch brief; flagging in case
  lex-verification or lex-doc wants an entry added.
