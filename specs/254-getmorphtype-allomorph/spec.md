# Spec — #254: `GetMorphType`/`SetMorphType` on `IWfiMorphBundle`

**Status:** CONTRACT FROZEN (spurt 1, cycle 1). Ready to implement.
**Target file:** `flexicon/code/TextsWords/WfiMorphBundleOperations.py`
**Live ground truth:** `evidence/live-cycle1-probe.md` (`run_mode: live`, Sena 3
via `sena3_sandbox`)

## The bug, in one line

`bundle.MorphRA` holds the bundle's **allomorph** (`IMoForm` — live: 697
`MoStemAllomorph` + 1142 `MoAffixAllomorph`, `None` on ~4.8%), not its morph
**type**. `GetMorphType` returns that field raw; `SetMorphType` assigns an
`IMoMorphType` into it. The real type is one hop further, at
`MorphRA.MorphTypeRA`.

## Decisive live findings that shaped the contract

- `SetMorphType(bundle, <IMoMorphType>)` is a **hard crash**, not silent
  corruption: `TypeError: SIL.LCModel.DomainImpl.MoMorphType value cannot be
  converted to SIL.LCModel.IMoForm`, raised before any mutation reaches the
  LCM. **The non-None write path has therefore never once succeeded.** No
  caller can depend on it; there is no corrupt data in the wild to migrate.
- The only path that ever functioned is `SetMorphType(bundle, None)`, which
  nulls `MorphRA` — i.e. clears the *allomorph* while the docstring claims it
  "clears the type reference".
- `MorphTypeRA.Name.get_String(anal_ws)` returns **empty** for all samples;
  `Name.BestAnalysisAlternative.Text` is what yields real strings
  (root/stem/prefix/suffix/enclitic). The current `GetMorphType` docstring
  example uses the empty-returning form.

## Frozen contract

### C1 — `GetMorphType(bundle_or_hvo)`: repair in place, do not rename

Returns `IMoMorphType | None`. Reads `bundle.MorphRA.MorphTypeRA`.

- `MorphRA is None` → **log a warning** naming the bundle `Hvo` (a bundle with
  no linked morph is a structurally incomplete analysis; the warning makes the
  gap discoverable) and return `None`.
- `MorphRA` set but `MorphTypeRA is None` → return `None` **silently**
  (ordinary, common).

This is the #232 pattern (wrong field read under a correct name), not the
Etymology pattern (renamed field) — so repair, don't rename or retire.
`AllomorphOperations.GetMorphType` (:871) already shows the correct sibling
read and needs no change.

Prefer bare `bundle.MorphRA.MorphTypeRA`: `MorphRA` is statically typed
`IMoForm` and `MorphTypeRA` is declared there, so it should be visible without
a cast. **Confirm live** — if bare access fails, use an explicit
`IMoForm(...)` cast and cite the 4.5.1 precedent (pythonnet attribute
visibility follows the static wrapper interface, not the runtime CLR type).

### C2 — `SetMorphType(...)`: retire unconditionally, **including the `None` form**

Raises `FP_ParameterError` on **every** call. Remove `_EnsureWriteEnabled()`,
the `_TransactionCM` block, and the `__GetMorphTypeObject` call. Raise
**first**, before any write-mode check, so the message is identical on
read-only and write-enabled projects.

The `None` form is retired too, and this is the one genuinely debatable call —
the ruling and its reasoning:

- What it did (null `MorphRA`) is *exactly* what `SetMorph(bundle, None)` will
  do, so no capability is lost.
- The name lies about which reference is cleared. Keeping it would preserve a
  method that clears an **allomorph** under a name saying **type** — the exact
  bug class #254 exists to eliminate — and would leave the pair asymmetric
  (getter reading `MorphTypeRA`, setter still writing `MorphRA`).
- A caller who wrote `SetMorphType(bundle, None)` believing the docstring was
  clearing the allomorph by accident. Silently preserving that is worse than a
  loud, actionable error at the call site.

No `DeprecationWarning` window (lex-domain's ranked option 2 is declined): a
soft landing exists to protect working callers, and the non-None path never
wrote anything, while the `None` path fails immediately and visibly rather
than corrupting.

The message must name **both** replacements, e.g.:

> `SetMorphType()` has been retired: it wrote its morph-type argument into
> `bundle.MorphRA`, which holds the bundle's allomorph (`IMoForm`), not its
> morph type — every non-`None` call raised `TypeError` at the .NET boundary
> and never wrote anything. To retype the lexicon allomorph, use
> `project.Allomorphs.SetMorphType(allomorph, morph_type)`. To change or clear
> which allomorph this bundle links, use `SetMorph(bundle, allomorph_or_None)`.

Keep the `morph_type_or_hvo` parameter in the signature so existing call sites
reach the explanatory error instead of a `TypeError` about arity; document it
as ignored.

### C3 — `GetMorph(bundle_or_hvo)`: new

Returns `bundle.MorphRA` (`IMoForm | None`) — today's buggy `GetMorphType`
behaviour, honestly named. `None` returns **silently, no warning**: reporting
"no morph linked" is this getter's job, whereas `GetMorphType` warns because a
missing morph blocks the resolution it was asked for.

Named `GetMorph`/`SetMorph` (not `GetAllomorph`): the field is `MorphRA`, the
house style drops the `RA`/`OA` suffix, and LCM itself calls this slot the
bundle's Morph. Docstring must state plainly that the object is the specific
allomorph (`IMoForm`), so `GetMorph(bundle) is not GetMorphType(bundle)` is
not a surprise.

### C4 — `SetMorph(bundle_or_hvo, morph_or_hvo)`: new

Writes `bundle.MorphRA = morph`. Accepts `None` to clear. Resolution stays
**outside** the transaction (existing house pattern in this file).

Add a private `__GetMorphObject` resolver documenting `IMoForm`; do **not**
reuse `__GetMorphTypeObject` (:1290), whose docstring correctly promises
`IMoMorphType`. If a non-`None` argument resolves to something that is not an
`IMoForm`, raise `FP_ParameterError` naming the received `ClassName` rather
than letting the raw pythonnet `TypeError` escape. This guard is what makes
C2's retirement actionable: a user who passes a morph type to `SetMorph` gets
our error, not `TypeError: ... cannot be converted to SIL.LCModel.IMoForm`.

### C5 — Docstring rewrite is part of the fix, not follow-up polish

The shipped `SetMorphType` **Example** (L845-849) instructs the caller to pull
`suffix_type` from `project.lp.MorphTypesOA.PossibilitiesOS` and pass it in —
the published documentation *is* the crash vector. Required corrections:

- **`SetMorphType`:** delete the whole Example block (both the assignment and
  the `SetMorphType(bundles[1], None)` line); replace with the retirement
  notice and a migration example. Fix `Args:` (stop documenting
  `IMoMorphType` as the accepted contract). Fix `Notes:` — "Setting to None
  clears the type reference" is false; it cleared the **allomorph**. Fix
  `See Also:` → `SetMorph`, `AllomorphOperations.SetMorphType`.
- **`GetMorphType`:** replace `morphType.Name.get_String(wsHandle)` with
  `Name.BestAnalysisAlternative.Text` (the former returns empty live — a fixed
  getter must not ship with an example that prints nothing). Document the
  `MorphRA is None` warning. Add `See Also:` → `GetMorph`.
- Drop the `"suffix" in str(mt).lower()` idiom: the shipped example modelled
  the very substring match that misses every prefix. Sweep for any other
  docstring reproducing either that idiom or the `MorphTypesOA.PossibilitiesOS`
  → bundle-assignment pattern.

Getter and setter currently lie **consistently** (`See Also:` pairs them), so a
set-then-get round-trip shows no discrepancy and self-confirms. Both sides must
land together.

### C6 — Release stance: BREAKING (behavioural), next minor. Sign-off resolved.

`GetMorphType`'s return type flips `IMoForm` → `IMoMorphType`. This is the only
part of the change with real back-compat surface (callers who chained
`.MorphTypeRA` themselves did have working code). Ships under `### Changed` in
`[Unreleased]` marked **BREAKING (behavioural)**, targeting the next **minor**
(4.6.0 from 4.5.2), no deprecation window.

Precedent, both breaking behavioural fixes shipped in minors: the
`OpenProject(..., undoable=...)` default flip (CHANGELOG L279-280) and #232's
`GetPartOfSpeechObject` repair. lex-domain's flag for human semver sign-off is
**resolved against the repo's documented stance** and does not gate
implementation; the version cut itself remains the user's call at tag time.

## Out of scope — file separately, do not fold in

- **Canonical-GUID morph-type classification helpers** (`is_prefix()` /
  `is_type()` against `MoMorphTypeTags.kguidMorph*`), replacing substring
  matching on type names for good. Additive; own issue.
- **`InflClassRA` existence on `IWfiMorphBundle`** —
  `GetInflectionClass`/`SetInflectionClass` (:1113/:1166) read and write it
  **unguarded**, while every other access in the codebase is `hasattr`-guarded
  (:326, :376 same file; `WfiAnalysisOperations.py:561`;
  `WordformOperations.py:878`), suggesting the field may not exist on this
  interface at all. Different Category 8 shape (unguarded access to a possibly
  nonexistent field, vs. wrong-field-under-right-name). Settle with one live
  reflection call while the LCM session is open, then **file its own issue if
  positive** — folding a second fix in would balloon the diff and muddy the
  CHANGELOG entry.

## Sweep result (closes the "are there more?" question)

111 `.py` files under `flexicon/code/`, four mechanical passes: the
`GetMorphType`/`SetMorphType` pair is the **entire population** of this shape.
The issue's own sweep hint resolves **negative** — `AllomorphOperations:871`
and `LexEntryOperations:1443` are both already correct.
`EtymologyOperations.GetLanguage`/`SetLanguage` (nonexistent `LanguageRA`) is
already documented and deliberately unfixed in Category 8. See
`reviews/cycle1-sweep.md`.
