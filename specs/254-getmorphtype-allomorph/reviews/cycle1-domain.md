# Domain Expert Review — Issue #254: morph-type access on IWfiMorphBundle

**Date:** 2026-09-06
**Domain:** FLEx / LCM linguistic data model (interlinear morphology)
**Status:** RECOMMENDATIONS READY — one item flagged for human sign-off

## Q1 — Fix GetMorphType, don't rename it

Repair, don't rename. This is the #232 pattern (name/docstring say one thing,
the field read returns the wrong object), not the Etymology pattern (field
silently renamed under an unchanged public name for the *same concept*).
Here the current code returns an `IMoForm` (the allomorph) under a method
named, documented, and typed as returning `IMoMorphType`. That's not a
renamed field — it's the wrong field entirely, and `AllomorphOperations.GetMorphType`
(L871, `allomorph.MorphTypeRA`) already shows the correct sibling pattern in
this same codebase. Fix `GetMorphType` to return `bundle.MorphRA.MorphTypeRA`
(guarding `bundle.MorphRA is None`). This is a breaking change for any caller
currently receiving the allomorph and manually chaining `.MorphTypeRA` — but
per #232, this repo prioritizes name-correctness over silent compatibility,
and the current behavior is unusable as documented (nobody calling this for
a "morph type" wants an `IMoForm`).

## Q2 — SetMorphType must not write to MorphRA

No FLEx user workflow "sets the morph type of a wordform's morph bundle."
In the Interlinear Texts tool, the analyst changes which **morph/allomorph**
a bundle points to (via "Change To…" / choosing a lexical entry's allomorph);
the type shown is *derived* from that allomorph's own `MorphTypeRA` in the
lexicon. There is no UI control that edits type independent of which
allomorph is linked — because doing so would retype the shared lexicon
allomorph for every other wordform-instance that references it. That is
almost certainly not what a caller means when they call
`SetMorphType(bundle, some_type)` at the analysis level.

Recommendation: **retire `SetMorphType`'s write path.** Two sub-options,
ranked:
1. **(Preferred)** Raise `FP_ParameterError` with a message directing callers
   to `AllomorphOperations.SetMorphType(allomorph, type)` if they intend to
   retype the lexicon entry, since that's the only place a morph type is
   legitimately owned.
2. Deprecate with a `DeprecationWarning` for one release, forwarding to the
   same error, before removal — only worth it if #254's fix needs a soft
   landing for existing callers.

Note for verification: assigning an `IMoMorphType` (an `ICmPossibility`
subtype, unrelated to `IMoForm`) into a property statically typed `IMoForm`
is likely to throw at the pythonnet/COM layer for any non-None value — so
today's `SetMorphType` may already be broken at runtime, not just
semantically wrong. This needs live-LCM confirmation, not assumption.

## Q3 — Add an honest GetMorph/SetMorph pair

Yes. Name them `GetMorph` / `SetMorph`, not `GetAllomorph`/`SetAllomorph`.
Reasons: (a) the underlying field is literally `MorphRA` — this repo's
sibling getters consistently drop the `RA`/`OA` suffix as the method name
(`SenseRA`→`GetSense`, `MSA`-family fields→`GetMSA`), so `Morph` is the
name-preserving choice; (b) LCM's own class is `WfiMorphBundle` referencing
a `Morph`, so "Morph" is the domain term FLEx itself uses at this level,
even though the concrete object is an allomorph (`IMoForm`). Document
plainly in the docstring that the returned/accepted object is the specific
allomorph (`IMoForm`) linked to this analysis, so users aren't confused when
`GetMorph(bundle) is not GetMorphType(bundle)`.

`SetMorph(bundle, allomorph_or_hvo)` is the method that legitimately writes
`bundle.MorphRA = allomorph` — this is the real, safe, analysis-level
operation the current buggy `SetMorphType` was reaching for.

## Q4 — None-collapsing needs a warning, not a new sentinel

Keep returning `None` for both cases (don't introduce a sentinel type — that
would break the simple optional-return contract every other `Get*` method in
this class uses). But the two `None`s are not equally suspicious, and #232
already established the fix for exactly this shape of ambiguity: log a
warning when `bundle.MorphRA is None` (a wordform morph bundle with *no
linked allomorph at all* is a structurally incomplete analysis — rare and
worth flagging), and return `None` silently when the allomorph is linked but
its own `MorphTypeRA` is simply unset (ordinary, common, not worth logging).
This mirrors the #232 note precisely: "a sense whose MSA has an unrecognized
ClassName now returns None and logs a warning... discoverable rather than
indistinguishable from 'no POS set.'"

## The "ffix in morphtype" substring trap

This stays out of scope for the `Get`/`Set` contract fix, but flag it:
once `GetMorphType` returns the real `IMoMorphType` object, callers should
never be doing substring matching on a name string at all (`"ffix" in
morphtype` was only possible because the buggy getter forced callers into
ad-hoc string workarounds). The correct long-term answer is a capability
check against canonical morph-type GUIDs (`MoMorphTypeTags.kguidMorph*` —
prefix, suffix, infix, stem, bound stem/root, circumfix, simulfix, etc.),
consistent with this repo's stated "capability checks instead of type
checking" design philosophy. Recommend tracking a follow-up
(`is_prefix()`/`is_type()` helper on a future morph-type wrapper) as a
separate issue rather than folding it into #254 — the immediate fix is
returning the correct object; classification helpers are additive.

## RECOMMENDED CONTRACT

| Method | Contract |
|---|---|
| `GetMorphType(bundle)` | Returns `bundle.MorphRA.MorphTypeRA` (`IMoMorphType` or `None`). Logs a warning if `MorphRA` itself is `None`. **Breaking change — see flag below.** |
| `SetMorphType(bundle, type)` | Raises `FP_ParameterError` directing callers to `AllomorphOperations.SetMorphType` (retype the lexicon allomorph) or the new `SetMorph` (repoint the bundle). Never writes `bundle.MorphRA` from a morph-type argument again. |
| `GetMorph(bundle)` *(new)* | Returns `bundle.MorphRA` (`IMoForm` or `None`) — today's buggy `GetMorphType` behavior, now honestly named. |
| `SetMorph(bundle, allomorph_or_hvo)` *(new)* | Resolves and writes `bundle.MorphRA = allomorph`, matching today's buggy `SetMorphType` behavior, now honestly named and type-correct. |

## FLAGGED FOR HUMAN DECISION

`GetMorphType`'s fix is a breaking behavior change (return type flips from
`IMoForm` to `IMoMorphType`). Confirm this repo's semver/release stance
(pre-1.0 vs. stable) before shipping, and whether a transitional
deprecation window is required for `SetMorphType` or whether an immediate
hard error is acceptable — this is a project/release-process call, not a
domain-semantics one.

---
**Reviewed By:** Domain Expert Agent (lex-domain, cycle 1)
**Domain:** FLEx / LCM linguistic data model
