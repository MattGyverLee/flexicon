# SPEC -- Phonological rule readers: environment, rule features, POSes, disabled, iteration/sequence contexts

**Status:** REVIEWED. Problem statement and LCM surface verified against a
live FieldWorks runtime; C1-C12 ruled on (interview answers, 2026-09-27) and
frozen. Not yet planned or implemented.
**Issue:** https://github.com/MattGyverLee/flexicon/issues/572
**Branch:** `fix/572-phonological-rule-readers` (worktree `C:/Github/flexicon-572`)
**Created:** 2026-09-27
**Evidence:** `specs/572-phonological-rule-readers/evidence/live-T1-surface.md`
(and the two machine-readable JSON files beside it)
**Constitution gates engaged:** I (verify the LCM surface), III (controls, not
prohibitions), V (honest API surface), VI (hide complexity, not behavior),
VII (expand freely; change the published surface only for cause)

---

## 1. Problem statement

The `PhonologicalRule` and `PhonologicalContext` wrappers expose `name`,
`direction`, `stratum`, `input_contexts`, `output_specs`, and each context's
`segment`, `natural_class` and `boundary_type`. A script that wants to
*describe* a rule -- what it changes, where it applies, what blocks it -- still
has to drop to raw LCM for the rest of it. Specifically missing: the rule's
environment (`IPhSegRuleRHS.LeftContextOA` / `RightContextOA`), the rule
features that block it (`ReqRuleFeatsRC` / `ExclRuleFeatsRC`), the POSes it is
limited to (`InputPOSesRC`), its disabled state (`IPhSegmentRule.Disabled`),
and the iteration / sequence context shapes (`IPhIterationContext`,
`IPhSequenceContext`).

The asymmetry is sharp and the direction is wrong. `WireRule` **writes** every
one of these -- `WireRule` sets `rhs.LeftContextOA` /
`rhs.RightContextOA` and builds `IPhSequenceContext` sequences with
`MembersRS` (`PhonologicalRuleOperations.py:997-1022`, `:1138-1166`) -- and
`MakeConstraint` creates `IPhFeatureConstraint`s that
`IPhSimpleContextNC.PlusConstrRS` / `MinusConstrRS` reference. There is no way
to read any of it back. flexicon can build a rule it cannot describe.

The two `SetLeftContext` / `SetRightContext` methods are not the gap. They
refuse with `NotImplementedError` and say so (issue #142,
`PhonologicalRuleOperations.py:639-700`); that is the surface being honest.
The gap is the absent getter beside them.

The issue's own evidence: in the FlexToolsMCP unified-recipes harvest
(2026-09-26), the `phonological-rules` recipe source (MCPlayground
`flex-parse-fixup/lib/phon_rules.py`, 44 lines) uses **no flexicon at all** --
13 casts across 10 `IPh*` / `ICmPossibility` types plus `ClassName` dispatch,
to print each rule with its contexts and exception features.

---

## 2. Verified LCM surface

Constitution Principle I: no item below is assumed. Every row was reflected
off a live FieldWorks 9 runtime and recorded in
`evidence/live-surface-probe.json`; the live values are in
`evidence/live-instance-probe.json`. `run_mode` was `"live"`
(`tests/live_status.json`).

### 2.1 Properties the issue names -- all confirmed

| Property | Declared on | Type | r/w |
|---|---|---|---|
| `LeftContextOA` | `IPhSegRuleRHS` | `IPhPhonContext` | r/w |
| `RightContextOA` | `IPhSegRuleRHS` | `IPhPhonContext` | r/w |
| `StrucChangeOS` | `IPhSegRuleRHS` | `ILcmOwningSequence<IPhSimpleContext>` | r |
| `ReqRuleFeatsRC` | `IPhSegRuleRHS` | `ILcmReferenceCollection<IPhPhonRuleFeat>` | r |
| `ExclRuleFeatsRC` | `IPhSegRuleRHS` | `ILcmReferenceCollection<IPhPhonRuleFeat>` | r |
| `InputPOSesRC` | `IPhSegRuleRHS` | `ILcmReferenceCollection<IPartOfSpeech>` | r |
| `OwningRule` | `IPhSegRuleRHS` | `IPhRegularRule` | r |
| `Disabled` | **`IPhSegmentRule`** | `System.Boolean` | r/w |
| `StrucDescOS` | **`IPhSegmentRule`** | `ILcmOwningSequence<IPhSimpleContext>` | r |
| `RightHandSidesOS` | `IPhRegularRule` only | `ILcmOwningSequence<IPhSegRuleRHS>` | r |
| `Minimum` | `IPhIterationContext` | `System.Int32` | r/w |
| `Maximum` | `IPhIterationContext` | `System.Int32` | r/w |
| `MemberRA` | `IPhIterationContext` | `IPhPhonContext` | r/w |
| `MembersRS` | `IPhSequenceContext` | `ILcmReferenceSequence<IPhPhonContext>` | r |
| `ItemRA` | `IPhPhonRuleFeat` | `ICmObject` | r/w |
| `FeatureStructureRA` | `IPhSimpleContextSeg` | `IPhPhoneme` | r/w |
| `FeatureStructureRA` | `IPhSimpleContextNC` | `IPhNaturalClass` | r/w |
| `FeatureStructureRA` | `IPhSimpleContextBdry` | `IPhBdryMarker` | r/w |
| `PlusConstrRS` / `MinusConstrRS` | `IPhSimpleContextNC` | `ILcmReferenceSequence<IPhFeatureConstraint>` | r |

Corroborating FieldWorks source, cited per `CLAUDE.md`:

- `Minimum` / `Maximum` / `MemberRA`:
  `Src/LexText/ParserCore/HCLoader.cs:2341-2343`,
  `Src/LexText/Morphology/RuleFormulaVcBase.cs:520-554`,
  `Src/LexText/Morphology/RegRuleFormulaControl.cs:731-742, 813-814`.
- `IPhPhonRuleFeat.ItemRA`:
  `Src/LexText/ParserCore/HCLoader.cs:2610-2623`,
  `Src/LexText/ParserCore/ParserCoreTests/HCLoaderTests.cs:405-411`.
- The three RC collections, written and read together:
  `ParserCoreTests/HCLoaderTests.cs:1084-1086` (write) and
  `HCLoader.cs:2052-2058` (read).

### 2.2 Two corrections to the issue text

1. **`IPhPhonRuleFeat.FeatureStructureRA` does not exist.** `IPhPhonRuleFeat`
   declares exactly one property, `ItemRA` (type `ICmObject`), and implements
   `ICmPossibility`. The issue lists it in both the problem statement and the
   proposal. Nothing in the design may depend on it -- see C5 for what
   replaces it.
2. **`PhBoundaryContext` / `IPhBoundaryContext` do not exist.** The real class
   is `PhSimpleContextBdry` / `IPhSimpleContextBdry`, whose only property is
   `FeatureStructureRA : IPhBdryMarker`. The string `PhBoundaryContext` occurs
   nowhere in the FieldWorks source tree
   (`rg -c PhBoundaryContext C:/Github/fieldworks/Src` -> no match, exit 1); it
   occurs only in flexicon. flexicon's current
   `PhonologicalContext.is_boundary_context` tests for it -- see C7.

### 2.3 Ownership, measured

`IPhSegRuleRHS.OwningRule` is typed `IPhRegularRule`, and
`IPhMetathesisRule` has no `RightHandSidesOS` and therefore no RHS and
therefore no environment at all. It carries `StrucChange` (a single context)
in place of `StrucChangeOS`. A metathesis rule is not a rule with an empty
environment; it is a rule whose environment is expressed by its switch indices
(`LeftSwitchIndex` / `LeftSwitchLimit` / `RightSwitchIndex` /
`RightSwitchLimit`, which `PhonologicalRule.metathesis_parts` already handles).

`PhonologicalDataOA.ContextsOS` is the project-wide owner pool for sequence
members, and `PhonologicalDataOA.PhonRuleFeatsOA.PossibilitiesOS` is the owner
list for rule features. Both confirmed live:
`ContextsOS` holds 7 members in `morphboundary`
(`PhSimpleContextBdry`, `PhSimpleContextSeg`); `PhonRuleFeatsOA` is a
`CmPossibilityList` in all five projects probed.

### 2.4 The narrowing trap, measured

pythonnet narrows an object to the interface its owning collection yields, so
`hasattr` against a raw element is unsound:

| Object, as reached | pythonnet proxy type | `hasattr` |
|---|---|---|
| `PhonologicalDataOA.PhonRulesOS[i]` | `IPhSegmentRule` | `RightHandSidesOS` -> **False** |
| the same, after `cast_to_concrete` | `IPhRegularRule` | `RightHandSidesOS` -> **True** |
| `rule.StrucDescOS[i]` | `IPhSimpleContext` | `FeatureStructureRA` -> **False** |
| `rhs.LeftContextOA` / `RightContextOA` | `IPhPhonContext` | `FeatureStructureRA` -> **False** |

`IPhSimpleContext` declares zero properties. `IPhPhonContext` declares only
`Name` and `DescriptionOA`. Every context's content lives on its concrete
interface. The wrapper base already handles this
(`Shared/wrapper_base.py:149` -- `self._concrete = cast_to_concrete(lcm_obj)`),
so the constraint is already the house rule; it is stated as C10 because the
new readers are exactly the members most likely to get it wrong.

---

## 3. Contract items (FROZEN)

Each item is a decision, and each has been ruled on. The fact behind it was
already measured in section 2; the ruling is recorded in brackets.

### C1 -- The environment lives on the RHS, and the RHS is indexed

`LeftContextOA` and `RightContextOA` are properties of `IPhSegRuleRHS`, and a
rule has *N* right-hand sides (`RightHandSidesOS` is an owning sequence). A
rule therefore has one environment per RHS, not one environment.

**Ruled (2026-09-27).** `PhonologicalRuleOperations` gains
`GetLeftContext(rule_or_hvo, rhs_index=0)` and
`GetRightContext(rule_or_hvo, rhs_index=0)`, each returning a
`PhonologicalContext` or `None`. **Ruling Q4: both surfaces ship** -- the
wrapper property is the primitive and the `Operations` reader delegates to it,
so there is one implementation and two entry points. `rhs_index` defaults to
`0` because `WireRule` only ever writes index 0 and a single-RHS rule is the
overwhelming norm; the parameter exists so a multi-RHS rule is readable, not
because multi-RHS is common.

`PhonologicalRule` gains `left_context(rhs_index=0)` and
`right_context(rhs_index=0)` delegating to the same code path, matching the
existing wrapper-plus-reader precedent (`GetStratum` / `.stratum`,
`GetDirection` / `.direction`).

**Returns a wrapper, not a raw object.** This is the one place the rule in C8
does not apply, and the reason is measured: `IPhSimpleContext` declares no
properties, so a raw context object handed to a caller is unusable without the
cast flexicon is supposed to hide. Wrapping is the deliverable, not a
convenience.

**Ruling R2 confirmed: separate left/right getters, no `GetEnvironment()`
record type.** The names mirror the `SetLeftContext` / `SetRightContext` pair
they fill in, and a record type would be a second new published name to
maintain beside the `PhonologicalContext` and `RuleFeatureCollection` names
this feature already introduces.

**Out of scope, explicitly:** any writer. `SetLeftContext` /
`SetRightContext` stay refused (#142); `WireRule` remains the only composer.

### C2 -- A metathesis rule reports no environment, and does not raise

`IPhMetathesisRule` has no `RightHandSidesOS`, so it has no RHS, so it has no
`LeftContextOA` / `RightContextOA`. There is nothing to return.

**Ruled (2026-09-27), silent.** `GetLeftContext` / `GetRightContext` return
`None` for a metathesis rule, and `PhonologicalRule` gains `has_environments`
so a caller can ask before asking. **Ruling Q2: no `warnings.warn`.** A
caller iterating `GetAll()` would get one warning per metathesis rule per
call, and `has_environments` already makes the case explicit. Per
`docs/API_DESIGN_PHILOSOPHY.md` rule 4 the capability check replaces a
`ClassName` test; per rule 6 the consequence is shown rather than enforced --
nothing is blocked, the environment is simply absent, and a metathesis rule's
environment is reachable through `metathesis_parts`. The absence of a warning
is deliberate and documented on both methods, so the silence is a stated
contract rather than an oversight.

Returning `None` rather than raising is the same choice
`GetStratum` already makes when `StratumRA` is unset
(`PhonologicalRuleOperations.py:522-524`).

### C3 -- Readers return the LCM object where the LCM collection is already typed

`ReqRuleFeatsRC`, `ExclRuleFeatsRC` and `InputPOSesRC` are *typed* reference
collections -- `ILcmReferenceCollection<IPhPhonRuleFeat>` and
`...<IPartOfSpeech>`. Iterating them yields the concrete interface with no
cast, and casting or re-wrapping would only cost the caller the object.

**Ruled (2026-09-27).** `GetInputPOSes(rule_or_hvo, rhs_index=0)` returns
`list[IPartOfSpeech]`. `GetRequiredRuleFeatures` /
`GetExcludedRuleFeatures` return the `IPhPhonRuleFeat` objects, and
`PhonologicalRule` wraps them in a smart collection whose `names` property
gives the strings, so both forms are one call apart without two parallel
method families.

This is the "maximize functionality in simple queries" rule
(`docs/API_DESIGN_PHILOSOPHY.md` rule 2) applied to a collection the LCM has
already done the work for. It is the same shape as `GetStratum`, which returns
`IMoStratum` rather than a string.

### C4 -- Rule features are possibilities; their name is their own, and their subject is `ItemRA`

`IPhPhonRuleFeat` implements `ICmPossibility` and declares only `ItemRA`. So:

- the rule feature's **name** is its own `Name` (`ICmPossibility.Name`, an
  `IMultiString`);
- `ItemRA` is the thing it constrains, and it is polymorphic:
  `IMoInflClass` or another `ICmPossibility`
  (`HCLoader.cs:2612-2622` dispatches on exactly those two `ClassID`s);
- the possibility list that owns them all is
  `PhonologicalDataOA.PhonRuleFeatsOA.PossibilitiesOS`.

**Ruled (2026-09-27).** The `PhonRuleFeat` wrapper exposes `name` (its own
possibility name) and `item` / `item_name` (the `ItemRA` target and that
target's name), and the collection exposes `names`. A caller asking "what
blocks this rule" gets names; a caller asking "what does that feature
constrain" gets the object.

**C4 correction carried from 2.2.** The issue's
`IPhPhonRuleFeat.FeatureStructureRA` is not used, does not exist, and is not
substituted. `ItemRA` is the only link.

### C5 -- Iteration contexts: `min_count`, `max_count`, `member`; unbounded is `None`

`IPhIterationContext` declares `Minimum : Int32`, `Maximum : Int32`,
`MemberRA : IPhPhonContext`, all read/write. FieldWorks renders
`Maximum == -1` as infinity
(`Src/LexText/Morphology/RuleFormulaVcBase.cs:554`:
`ctxt.Maximum == -1 ? m_infinity : ...`).

**Ruled (2026-09-27).** `PhonologicalContext` gains `is_iteration_context`,
`min_count : int`, `max_count : Optional[int]`, and `member`, and
`max_count` returns `None` for `-1`.

`None` rather than `-1` because a sentinel that means "no limit" is an LCM
encoding detail, and Principle VI says hide complexity but not behaviour: the
*behaviour* is "this repeats without limit", which `None` states. The
docstring says `None` means unbounded and cites the `-1` source. The raw value
is not separately exposed -- one property, one meaning.

**Ruling R3 confirmed: no `maximum_raw`.** A caller porting from raw LCM and
expecting `-1` gets `None` and must adjust; the docstring is the contract.

### C6 -- Sequence contexts: `members`, and the members are references

`IPhSequenceContext.MembersRS` is `ILcmReferenceSequence<IPhPhonContext>`. The
members are *references* into `PhonologicalDataOA.ContextsOS`, not owned
children of the sequence -- that is why `WireRule.__WireContext` parks each
member in the pool and then only references it, and why nulling the slot leaks
members unless they are explicitly removed (#134,
`PhonologicalRuleOperations.py:1042-1082`).

**Ruled (2026-09-27).** `PhonologicalContext` gains `is_sequence_context` and
`members`, returning a `ContextCollection` of wrapped `PhonologicalContext`
objects, so a caller walks a multi-element environment the same way they walk
`input_contexts`. The docstring states that the members live in the project
pool, because a caller who plans to write will otherwise leak them.

### C7 -- Three members of the current surface are dead, and the new readers must not inherit their shape

All three were measured, not inferred (evidence §"Two dead members").

1. **`is_boundary_context`, `boundary_type`, `as_boundary_context()`, and
   `ContextCollection.boundary_contexts()` match `"PhBoundaryContext"`, a
   class that does not exist.** They are always `False` / `None` / empty. Real
   boundary contexts are `PhSimpleContextBdry`, and `morphboundary` has two of
   them in its pool and one as a rule's left context. `boundary_type` compounds
   it by reading `.Type`, which `IPhSimpleContextBdry` does not declare; the
   boundary's identity is the `IPhBdryMarker` behind `FeatureStructureRA`.
2. **`context_name` returns `"SIL.LCModel.DomainImpl.MultiUnicodeAccessor"`.**
   It does `str(Name)`, and `Name` on `IPhPhonContext` is an `IMultiString`.
   Every live context returns that same literal string, so
   `ContextCollection.filter(name_contains=...)` -- which filters on
   `context_name` (`context_collection.py:151`) -- can never match.
3. **`description` returns `""` for every context type.** It reads
   `.Description`; no `IPhPhonContext` declares it. The only candidate is
   `DescriptionOA`, an `OwningAtomic` of type `IPhPhonContext`.

**Ruled (2026-09-27), silently.** Fix all three as part of this feature,
because the issue's deliverable -- "print each rule with its contexts and
exception features" -- is impossible while `is_boundary_context` cannot fire
and `context_name` is a type name. Principle V: an API that implies a
guarantee it does not deliver is already a defect whether or not a new issue
cites it.

- `is_boundary_context` tests `"PhSimpleContextBdry"`.
- `boundary_type` is replaced by a `boundary_marker` property returning the
  `IPhBdryMarker`, and a `boundary_name` property returning its text. The name
  `boundary_type` is retired: it promised a discriminator the LCM does not
  have, and every call site is a docstring. **Ruling Q3: no
  `DeprecationWarning`.** `PhonologicalContext` is internal, so the retirement
  is silent; a warning would fire on a class no importer can name from
  `flexicon`'s `__all__`. `docs/USAGE_CONTEXTS.md` carries 5 `boundary_type`
  mentions and 8 `PhBoundaryContext` mentions and MUST be updated in the same
  commit (Quality Gate 4).
- `context_name` reads `Name.BestAnalysisAlternative.Text` and returns `""`
  when unset.
- `description` reads `DescriptionOA` and returns its `Name` text, or `""`.

`PhonologicalContext` and `ContextCollection` are **not** in
`flexicon/__init__.py`'s `__all__` (only `PhonologicalRuleOperations` is, at
`flexicon/__init__.py:505`), so under constitution Principle VII 2.1.0 these
are internal and may be changed freely. `docs/USAGE_CONTEXTS.md` documents all
four names and MUST be updated in the same commit (Quality Gate 4).

### C8 -- Two corrections to the issue's proposed shape

- The issue names `IPhPhonRule` in neither place, but flexicon's own docstrings
  do, repeatedly (`PhonologicalRuleOperations.py:89, 174, 246, 353, 397, ...`).
  The real base is `IPhSegmentRule` (verified: `IPhPhonRule` does not reflect;
  `IPhSegmentRule` does, and `IPhRegularRule` / `IPhMetathesisRule` both
  implement it). Docstrings are corrected as they are touched.
- The issue's `IsDisabled` / `SetDisabled` for phonological rules is sound, and
  `MorphRuleOperations.IsDisabled` / `SetDisabled`
  (`MorphRuleOperations.py:813-880`) is the shape to mirror, including its
  `hasattr` guard held *outside* the transaction bracket. `Disabled` is declared
  on the base `IPhSegmentRule`, so the guard is belt-and-braces rather than
  load-bearing.

### C9 -- `Disabled` is read but not yet synced; that gap is closed here

`PhonologicalRuleOperations.GetSyncableProperties` emits `Name`,
`Description`, `Direction` and `StratumGuid` -- and not `Disabled`
(`PhonologicalRuleOperations.py:1506-1528`). A disabled rule therefore syncs
into the target project as enabled.
**Ruled (2026-09-27): ship here.** Add `"Disabled": rule.Disabled` to that
dict, and register it in `BaseOperations.ApplySyncableProperties`, whose
generic shape handling this class already delegates to
(`PhonologicalRuleOperations.py:1531-1538`).

The plan must expect to update any sync test that pins the exact key set, and
must report the offline-gate arithmetic for that change per Principle IV
(baseline: `2575 passed, 1081 deselected`). The key is additive to the dict's
shape but observable to anything reading sync metadata.

The item is here rather than omitted because leaving a newly-added reader's
value out of sync is exactly the half-delivery Quality Gate 4 exists to catch:
`IsDisabled` would report `True` in the source project and the target would
still parse with the rule enabled.

### C10 -- Every reader goes through a wrapper or casts; no `hasattr` on a raw element

Stated as a constraint because the new members are the most likely place to
get it wrong, and because `docs/API_DESIGN_PHILOSOPHY.md` rule 4's
capability checks are `hasattr`-shaped and therefore only sound on a cast
object (section 2.4).

**Ruled (2026-09-27).** Every capability check runs against
`self._concrete` (already cast by `LCMObjectWrapper.__init__`) or against an
explicit `cast_to_concrete` result. No new member reads an attribute off a
raw collection element.

Per Principle III this ships as a control, not as an instruction: a test that
wraps a live `PhSimpleContextBdry` and a live `PhSequenceContext` and asserts
both report their contents.

### C11 -- `DescribeRule` is included, at lowest priority, and is total

The issue offers `DescribeRule(rule) -> str` as optional, rendering
`input -> output / left _ right`, and observes that every script ends up
building it by hand.

**Ruled (2026-09-27).** Include it, as a method on
`PhonologicalRuleOperations`, as the last item. "Total" is the whole
requirement: it must produce a string for a metathesis rule, for a rule with no
RHS, for a rule with no contexts, and for a rule whose contexts include
iteration and sequence shapes, and it must never raise. A describe function
that raises on an unusual rule is the same defect in a new place.

`max_count is None` renders as `*` (unbounded), not `-1`.

### C12 -- Test data must be constructed for two of the readers

Measured across five installed projects: **no project on this machine holds an
`IPhIterationContext` or an `IPhPhonRuleFeat`.** `morphboundary` is the only
one of the five with any phonological rules at all (4 rules, 7 pooled
contexts), and it has no rule features and no iteration contexts.

**Ruled (2026-09-27).** Environment, `Disabled`, sequence-context and
boundary-context readers are verified against `morphboundary` read-only.
Iteration-context and rule-feature readers are verified against data a test
builds on **Target** (capture-and-restore in `finally:`, `TEST_` prefix) or in
a sandbox. This is a planning constraint, not an option, and it is the reason
C5, C6 and C4 carry write-path verification obligations.

Two further measured facts that affect planning:

- **Target and Sena 3 both have `PhonologicalDataOA` but zero rules**, and
  `PhonologicalDataOA.ContextsOS` and `PhonRuleFeatsOA.PossibilitiesOS` are
  both empty. Neither is a source of pre-existing phonological data.
- **Sena 3 opens cleanly and has zero phonological rules.** This contradicts
  `specs/326-phonological-wrapper-members/evidence/live-T1-reflection.md`,
  which recorded Sena 3 as unopenable on 2026-09-22. That finding is stale and
  is corrected here rather than carried forward; nothing in this feature
  depends on which is right, because Sena 3 has no phonological data either
  way.

---

## 4. Alternatives considered and NOT adopted (with the ruling that closed each)

The interview of 2026-09-27 ruled on all four, each in favour of what this
spec proposes. They are recorded rather than deleted, because the losing
option is the one a future reader will ask about.

- **R1 -- wrapper-only placement.** Rejected. The issue asks for HVO-accepting
  readers explicitly, and `MorphRuleOperations.IsDisabled` is the precedent a
  caller reaches for. **Ruling Q4: both surfaces ship** (C1), wrapper as the
  primitive. The duplication cost is accepted; it is one delegating method per
  reader, and the wrapper is internal so there is no published-surface cost
  beyond the `Operations` methods.
- **R2 -- one `GetEnvironment(rule, rhs_index=0)` returning a small record,
  instead of separate left/right getters.** Rejected. `GetLeftContext` /
  `GetRightContext` mirror the `SetLeftContext` / `SetRightContext` pair they
  fill in, and a record type would be a third new published name to maintain
  beside `PhonologicalContext` and `RuleFeatureCollection`. **Ruling Q4:
  separate getters.**
- **R3 -- expose `maximum` raw (`-1`) alongside `max_count` (`None`).**
  Rejected on Principle VI grounds: two properties for one value, one of them
  leaking an LCM encoding detail. **Confirmed in C5.**
- **R4 -- companion writers (`SetInputPOSes`, `SetRequiredRuleFeatures`).**
  Out of scope, **confirmed** rather than adopted: `WireRule` remains the only
  composer (#142). If writers are wanted they are their own feature, with
  their own live-write verification.

Also rejected, from the Q2 answer: raising `FP_ParameterError` on a metathesis
rule (it would block a read-only query against a perfectly valid rule class),
and warning on it (per-call noise inside a `GetAll()` loop).

Also rejected, from the Q3 answer: keeping the name `boundary_type` with a
fixed body (the name promises a discriminator the LCM does not have), and a
one-release `DeprecationWarning` on a class that is not in `__all__`.

Also rejected, from the Q1 answer: deferring the `Disabled` sync key to a
follow-up, and adding the key without the reader.

## 5. Open questions

**None.** All four asked on 2026-09-27 were answered, each confirming the
proposal: Q1 ship the `Disabled` sync key here (C9), Q2 return `None` silently
plus `has_environments` (C2), Q3 retire `boundary_type` silently (C7), Q4 both
surfaces with the wrapper as primitive (C1).

Two further questions were considered and closed without a vote, because the
spec can answer them from facts already measured:

- **C-Q4a. Export `RuleFeatureCollection` in `flexicon/__init__.py.__all__`?**
  Closed: **no.** Follow `ContextCollection`, which is internal. Exporting it
  would be a new published name needing a generated surface-baseline entry and
  a ratchet update, for a class callers reach through `GetAll()`-returned
  wrappers. (C3.)
- **C-Q4b. Does `has_environments` need an `Operations` mirror?** Closed:
  **wrapper only.** It is a cheap boolean over an existing member, and
  `PhonologicalRuleOperations` stays deliberately small. (C2.)

## 6. Contradictions checked for -- two found, both recorded, neither requiring side-by-side preservation

- The issue proposes `IPhPhonRuleFeat.FeatureStructureRA`; it does not exist
  (2.2.1). Resolved in C4 by using `ItemRA`. The issue's text is not edited.
- The issue is silent on metathesis rules; `IPhMetathesisRule` has no
  environment to read (2.3). Resolved in C2.

## 7. Success criteria

Measured against the baseline recorded in
`evidence/live-T1-surface.md` (`2575 passed, 1081 deselected` offline).

- **SC-001.** A script can print every rule in a project with its input
  contexts, output, environment, required and excluded rule features, input
  POSes and disabled state, using `flexicon` only -- no `IPh*` import, no
  `ClassName` test, no manual cast. Verified by a live test against
  `morphboundary`.
- **SC-002.** Zero `PhBoundaryContext`, `IPhBoundaryContext` or
  `IPhPhonRuleFeat.FeatureStructureRA` strings remain in `flexicon/code/` or
  `docs/`, outside the evidence file that records their non-existence. (C7,
  2.2.)
- **SC-003.** The `PhonologicalRule` wrapper's `input_contexts`,
  `output_specs` and `metathesis_parts` return byte-identical results before
  and after this change, measured on the same four `morphboundary` rules. A
  reader added next to an existing one that shifts is a regression, not an
  addition.
- **SC-004.** `context_name` returns the context's own name, or `""` -- never a
  .NET type name. `is_boundary_context` is `True` for a live
  `PhSimpleContextBdry`. Both measured on `morphboundary`.
- **SC-005.** `DescribeRule` returns a non-empty string for all four
  `morphboundary` rules, for a metathesis rule, and for a rule with no RHS,
  with no exception raised.
- **SC-006.** Offline gate: `python -m pytest -m "not requires_live_project" -q`
  is at least `2575 passed` with zero new failures. Any delta is reported with
  its arithmetic, per Principle IV.
- **SC-007.** Live gate: `FLEXLIBS_REQUIRE_LIVE=1` run of the new live test
  file shows `"run_mode": "live"` in `tests/live_status.json`, and every write
  in it is re-queried from the LCM after the write, with pre-state and
  post-state recorded in `specs/572-phonological-rule-readers/evidence/`.
- **SC-008.** Iteration-context and rule-feature readers each have a live test
  that constructs the data, reads it back, and restores -- because no installed
  project has any (C12).

## 8. Assumptions

- FieldWorks 9 with a live SIL.LCModel, as this machine has. The surface in
  section 2 is the 9.x surface; nothing here is claimed about other majors.
- `PhonologicalRuleOperations` is the published class
  (`flexicon/__init__.py:505`); every method added to it is additive growth
  under Principle VII and needs only a regenerated surface baseline.
- `PhonologicalRule`, `PhonologicalContext` and `ContextCollection` are
  internal (`flexicon/code/**`, not in `__all__`) and are changed freely.
- `docs/USAGE_CONTEXTS.md` is the reference that documents the four C7 names
  and is updated in the same commit.
- The FlexToolsMCP `phonological-rules` recipe (the issue's evidence) is the
  acceptance shape: print each rule with contexts and exception features. It is
  not built here; SC-001 is the check that flexicon could serve it.
- No writer is added for any member C1-C6 touches (`WireRule` remains the only
  composer, per #142).
