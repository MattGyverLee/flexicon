# Cycle 1 -- Domain / API Design Review (#256, with #253 contract question)

Agent: lex-domain
Feature: specs/feature-structure-sync-gap
Scope: read-only design review, no code changes.

> NOTE: lex-domain has no Write tool in its agent definition; this report was
> persisted verbatim by the main session on the agent's behalf.

## Summary

Both `MakeFeatStruc` implementations are code-identical (hardcoded `.FeaturesOA`,
flat specs) but diverge in *correctness*: `PhonFeatureOperations` happens to work
because its targets genuinely have `FeaturesOA`; `InflectionFeatureOperations`'
advertised MSA targets do not. Recommend a generalized, slot-disambiguated
owner-resolver, a recursive dict spec surface, `CopyFeatStruc` sharing that
resolver, `TypeRA` preserved-if-present, and RAISE as the frozen error contract
(already precedented and reasoned-through in
`NaturalClassOperations.ApplySyncableProperties`).

## A. Nesting surface

`("noun agreement", [(feat, val), ...])` is a silent isinstance-branch overload
(second element sometimes a value, sometimes a list) -- not self-documenting, and
it caps at exactly one extra level; Bantu agreement can in principle nest further
(`FsComplexValue.ValueOA` is itself a full `IFsFeatStruc`). Ship a **recursive
dict** surface instead -- nesting is literally Python nesting, matches FLEx's own
bracket notation `[noun agreement:[class:1 number:sg]]`, and has no depth limit:

```python
project.InflectionFeatures.MakeFeatStruc(
    specs={
        "noun agreement": {"class": "1", "number": "sg", "person": "3"},
    },
    owner=msa,
)
```

A dict value -> nested `IFsComplexValue`/`IFsFeatStruc`; a scalar value ->
`IFsClosedValue`. Keep the flat list-of-tuples as an accepted legacy alias,
documented as non-canonical.

## B. Owner-property resolution

Auto-resolve by `ClassName` for the 95% single-property case (hides interface
complexity, per philosophy) -- but `IMoDerivAffMsa` is genuinely ambiguous
(`FromMsFeaturesOA`/`ToMsFeaturesOA`) and must never be guessed.

```python
def MakeFeatStruc(self, specs, owner, slot=None):
    """
    slot: disambiguates when owner exposes >1 owning feature-struct
    property (currently only IMoDerivAffMsa: slot="From"/"To" ->
    FromMsFeaturesOA/ToMsFeaturesOA). Ignored for single-property
    owners. Raises FP_ParameterError naming the valid slot values
    when owner is ambiguous and slot is omitted.
    """
```

Internal resolver table: `MoInflAffMsa->InflFeatsOA`,
`MoStemMsa->MsFeaturesOA`, `MoDerivAffMsa->{From,To}MsFeaturesOA`,
`PhNCFeatures->FeaturesOA`. Single-property owners are unaffected.

## C. CopyFeatStruc location

Belongs in **InflectionFeatureOperations**, delegating to the same shared
owner-resolver as B (the attach step is identical regardless of source domain),
with the actual recursive-copy logic factored into a shared helper (alongside
`Shared/lcm_casting.clone_properties`) so `PhonFeatureOperations` can reuse it too
-- finally making the "mirrors PhonFeatureOperations" docstring claim literally
true instead of aspirational.

```python
def CopyFeatStruc(self, src_fs, target_owner, slot=None, overwrite=False):
    """
    Deep-copies src_fs onto target_owner's resolved owning property.
    Recurses through IFsComplexValue.ValueOA to arbitrary depth.
    Copies TypeRA at every level when the source has one (see E).

    overwrite=False (default): raise FP_ParameterError if the target's
    resolved property is already non-null (silent overwrite of an
    existing struct is itself a data-loss defect).
    overwrite=True: replace it (old struct is orphaned/discarded).
    """
```

Merge is intentionally **not** a mode: there is no unambiguous domain rule for a
conflicting `(feature, value)` at either nesting level -- that judgment belongs to
the linguist, not a silently-invented policy (warn-and-let-user-decide
philosophy).

## D. PhonFeatureOperations vs InflectionFeatureOperations

Byte-identical code, divergent correctness. `IPhNCFeatures.FeaturesOA` genuinely
exists, so `PhonFeatureOperations`' version works -- not because the design
generalizes, but by coincidence of a matching property name on its narrow target
set. `InflectionFeatureOperations` copied the pattern onto MSAs, which have no
`FeaturesOA` at all -- a textbook instance of the "same-name field, different type
or absent" trap CLAUDE.md already flags for issues #36/#39/#40. **Neither becomes
canonical as-is.** Extract one generalized `MakeFeatStruc(specs, owner, slot=None)`
into a shared location; make both existing methods thin call-throughs.

## E. TypeRA and FLEx display

`TypeRA` (on `IFsFeatStruc`/`IFsComplexValue`) points into the feature system's
`TypesOC` and is nullable by design -- it is a categorization/subsumption aid, not
a display driver. `LongName` is built from the populated features/values, not from
`TypeRA`, so a struct with null `TypeRA` renders and functions correctly in the
FLEx UI, consistent with the reporter's 0-mismatch `LongName` validation. Null
`TypeRA` is a faithful round-trip **only when the source also had null `TypeRA`**.
`CopyFeatStruc` must copy `TypeRA` by GUID-resolved reference whenever the source
has one -- dropping a populated `TypeRA` would be a silent fidelity bug even though
it would not show up in `LongName`.

## F. Error contract -- RAISE, family-wide

Adopt RAISE for the whole family, **including retrofitting PhonemeOperations**.
This is not a fresh call -- `NaturalClassOperations.ApplySyncableProperties`
already made and documented this exact decision, explicitly overriding
`PhonemeOperations`' skip as the bug-class being fixed (issue #222 lineage), not a
model to extend: silently dropping a spec yields a class/MSA whose *names* matched
but that matches nothing at rule-application time, discoverable only when a rule
mysteriously fails to fire. A linguist mid cross-project sync needs a synchronous
exception naming the unresolved feature/value GUID, instructing them to sync the
feature system first. `PhonemeOperations`' current skip-and-hope should not remain
the odd one out.

> LEAD DECISION REQUIRED: F recommends retrofitting `PhonemeOperations` (#253)
> in this pass, which is in tension with the cycle-1 plan's "adopt the contract,
> defer the edit" stance. Reconcile against the Explore sweep's shared-helper
> verdict (Deliverable 4) before freezing.
