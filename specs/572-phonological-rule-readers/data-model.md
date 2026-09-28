# Phase 1 Data Model: Issue #572 — phonological rule readers

The entities this feature adds or changes, over the already-verified LCM
surface in [spec.md](spec.md) §2. **No LCM type is introduced here** — every
field below maps to a member reflected off a live FieldWorks 9 runtime, cited
in the last column.

Scope: `RuleFeature` and `RuleFeatureCollection` are **new**;
`PhonologicalContext` and `ContextCollection` are **changed**;
`PhonologicalRule` and `PhonologicalRuleOperations` are **extended**.
Existing members are listed where a change could regress them.

---

## 1. `PhonologicalRule` (wrapper, internal) — EXTENDED

Owner of the reads. Lives in `flexicon/code/Grammar/phonological_rule.py`.
Reached by callers as `ruleOps.GetAll()[i]`, or via
`PhonologicalRuleOperations.GetLeftContext(rule)` and friends.

| Member | Type | Returns | Spec |
|---|---|---|---|
| `has_environments` | `bool` | `True` iff the rule is an `IPhRegularRule` with ≥1 RHS | C2 |
| `left_context(rhs_index=0)` | `Optional[PhonologicalContext]` | `rhs.LeftContextOA`, or `None` | C1 |
| `right_context(rhs_index=0)` | `Optional[PhonologicalContext]` | `rhs.RightContextOA`, or `None` | C1 |
| `input_poses(rhs_index=0)` | `list[IPartOfSpeech]` | `list(rhs.InputPOSesRC)`, `[]` if unset | C3 |
| `required_rule_features(rhs_index=0)` | `RuleFeatureCollection` | `ReqRuleFeatsRC` | C3, C4 |
| `excluded_rule_features(rhs_index=0)` | `RuleFeatureCollection` | `ExclRuleFeatsRC` | C3, C4 |
| `is_disabled` | `bool` | `rule.Disabled` | C8 |
| `set_disabled(disabled)` | `None` | writes `rule.Disabled` | C8 |

**Existing members that must not regress** (SC-003): `name`, `direction`,
`stratum`, `input_contexts`, `has_output_specs`, `output_specs`,
`has_metathesis_parts`, `metathesis_parts`, `has_redup_parts`, `redup_parts`,
`as_regular_rule`, `as_metathesis_rule`, `as_reduplication_rule`, `concrete`,
`__repr__`, `__str__` (`phonological_rule.py:129-537`).

### Validation rules

- `rhs_index` out of range → `IndexError`, not a silent `None`. A `None` for an
  out-of-range index is indistinguishable from "no environment", and C2 already
  gives callers a capability check for the latter.
- `rhs_index` on a metathesis rule → `None` from the context readers (C2), and
  `IndexError` from the collection readers only if the RHS list is genuinely
  empty **and** the rule claims to have environments. The `has_environments`
  check exists so a caller never has to distinguish these.
- `set_disabled` requires `project.writeEnabled`; raises `FP_ReadOnlyError`
  otherwise (`CLAUDE.md`, Write operations).

---

## 2. `PhonologicalRuleOperations` (published) — EXTENDED

`flexicon/code/Grammar/PhonologicalRuleOperations.py`. Every wrapper member
above gets a reader that accepts `rule_or_hvo` and delegates — the wrapper is
the primitive, per the Q4 ruling in spec §4.

| Reader | Signature | Delegates to | Returns |
|---|---|---|---|
| `GetLeftContext` | `(rule_or_hvo, rhs_index=0)` | `.left_context` | `Optional[PhonologicalContext]` |
| `GetRightContext` | `(rule_or_hvo, rhs_index=0)` | `.right_context` | `Optional[PhonologicalContext]` |
| `GetInputPOSes` | `(rule_or_hvo, rhs_index=0)` | `.input_poses` | `list[IPartOfSpeech]` |
| `GetRequiredRuleFeatures` | `(rule_or_hvo, rhs_index=0)` | `.required_rule_features` | `RuleFeatureCollection` |
| `GetExcludedRuleFeatures` | `(rule_or_hvo, rhs_index=0)` | `.excluded_rule_features` | `RuleFeatureCollection` |
| `IsDisabled` | `(rule_or_hvo)` | `.is_disabled` | `bool` |
| `SetDisabled` | `(rule_or_hvo, disabled)` | `.set_disabled` | `None` |
| `DescribeRule` | `(rule_or_hvo)` | — | `str` |

All eight resolve the argument with the class's existing `__ResolveObject`, so
`rule`, an HVO, and `None` behave as they do for `GetName` / `GetDirection`.
`None` raises `FP_NullParameterError`.

**`GetSyncableProperties` change** (C9): gains `"Disabled": rule.Disabled` as a
scalar, alongside the existing `Direction` int. `_apply_props_loop`
(`BaseOperations.py:459-...`) already handles `bool`/`int` scalars — its own
docstring at `BaseOperations.py:442` says "For bool/int: ALWAYS skipped when
`fill_gaps=True` — stored False/0 is a real choice, never overwrite" — so
**no base change is required**. Verified in research.md R-3 that
`test_syncable_properties_member_ratchet.py` does not scan this class (it
matches `hasattr(item, ...)`, and this class guards with `hasattr(rule, ...)`),
so no allowlist entry is needed either.

---

## 3. `PhonologicalContext` (wrapper, internal) — CHANGED + EXTENDED

`flexicon/code/System/phonological_context.py`. **The central entity**: six
members are repaired and six added.

### 3a. Repaired members

| Member | Was | Now | LCM source |
|---|---|---|---|
| `context_name` | `str(Name)` → a .NET type name | `best_analysis_text(Name)`, or `""` | `IPhPhonContext.Name` : `IMultiString` |
| `description` | `""` always (read a member that does not exist) | `best_analysis_text(DescriptionOA)`, or `""` | `IPhPhonContext.DescriptionOA` : `OwningAtomic<IPhPhonContext>` |
| `is_boundary_context` | always `False` | `class_type == "PhSimpleContextBdry"` | `PhSimpleContextBdry` |
| `boundary_type` | always `-1` | **retired** | member does not exist |
| `boundary_marker` | — (new) | `FeatureStructureRA` as `IPhBdryMarker`, or `None` | `IPhSimpleContextBdry.FeatureStructureRA` |
| `boundary_name` | — (new) | the marker's name text, or `""` | `IPhBdryMarker.Name` |
| `as_boundary_context()` | always `None` | `self._concrete` when `is_boundary_context` | `PhSimpleContextBdry` |

`as_boundary_context()` is repaired rather than retired: unlike `boundary_type`
its name is honest — it does return the concrete interface, which is what an
`*_as_*` method promises — and it is the parallel of the existing
`as_simple_context_seg` / `as_simple_context_nc` pair.

### 3b. New members

| Member | Type | Returns | LCM source | Spec |
|---|---|---|---|---|
| `is_iteration_context` | `bool` | `class_type == "PhIterationContext"` | concrete class | C5 |
| `min_count` | `int` | `Minimum`, or `-1` if not an iteration context | `IPhIterationContext.Minimum` : `Int32` | C5 |
| `max_count` | `Optional[int]` | `Maximum`, or `None` when `Maximum == -1` | `IPhIterationContext.Maximum` : `Int32` | C5 |
| `member` | `Optional[PhonologicalContext]` | `MemberRA`, or `None` | `IPhIterationContext.MemberRA` : `IPhPhonContext` | C5 |
| `is_sequence_context` | `bool` | `class_type == "PhSequenceContext"` | concrete class | C6 |
| `members` | `ContextCollection` | `MembersRS` | `IPhSequenceContext.MembersRS` : `ILcmReferenceSequence<IPhPhonContext>` | C6 |

**`max_count` sentinel rule** (C5, ratified): `Maximum == -1` means unbounded —
FieldWorks renders it as infinity at
`Src/LexText/Morphology/RuleFormulaVcBase.cs:554` (`ctxt.Maximum == -1 ?
m_infinity : ...`). The property returns `None`; the raw `-1` is not exposed.
The docstring is the contract and must state both.

**`members` ownership** (C6): the members are *references* into
`PhonologicalDataOA.ContextsOS`, not owned children — which is why
`WireRule.__WireContext` parks each in the pool and then only references it, and
why nulling the slot leaks members unless they are explicitly removed (#134,
`PhonologicalRuleOperations.py:1042-1082`). The docstring must say so, because
a caller who plans to write will otherwise leak.

### 3c. Unchanged, and must not regress (SC-003)

`is_simple_context_seg`, `is_simple_context_nc`, `is_simple_context`,
`is_complex_context_seg`, `is_complex_context_nc`, `is_complex_context`,
`segment`, `natural_class`, `as_simple_context_seg`, `as_simple_context_nc`
(`phonological_context.py:162-439`).

---

## 4. `RuleFeature` (wrapper, internal) — NEW

`flexicon/code/System/rule_feature.py`. Wraps one `IPhPhonRuleFeat`, which
implements `ICmPossibility` and declares exactly **one** property, `ItemRA`
: `ICmObject`.

| Member | Type | Returns | Basis |
|---|---|---|---|
| `name` | `str` | the possibility's own name, or `""` | `ICmPossibility.Name` |
| `item` | `Optional[object]` | `ItemRA`, or `None` | `IPhPhonRuleFeat.ItemRA` |
| `item_name` | `str` | the `ItemRA` target's name, or `""` | polymorphic — see below |

**`ItemRA` is polymorphic and the wrapper must not assume a type.** It is an
`IMoInflClass` or another `ICmPossibility`; FieldWorks dispatches on exactly
those two `ClassID`s at `Src/LexText/ParserCore/HCLoader.cs:2612-2622`, and
`ParserCoreTests/HCLoaderTests.cs:405-411` sets only `ItemRA` when building one.
So `item` returns the object uncast, and `item_name` reads `.Name` through
`best_analysis_text` on whatever it turns out to be.

**The issue's `FeatureStructureRA` is not modelled.** It does not exist on
`IPhPhonRuleFeat` (spec §2.2.1). Nothing in this entity references it.

---

## 5. `RuleFeatureCollection` (smart collection, internal) — NEW

`flexicon/code/System/rule_feature.py`, same module. Subclasses
`SmartCollection` (`Shared/smart_collection.py`), exactly as `ContextCollection`
does.

| Member | Type | Returns |
|---|---|---|
| `names` | `list[str]` | `[f.name for f in self]` |
| `items` | `list[object]` | the `ItemRA` targets, uncast |

**Not exported** in `flexicon/__init__.py`'s `__all__` (spec §5, C-Q4a):
follows `ContextCollection`, which is internal. Reached through
`PhonologicalRule.required_rule_features`.

`names` is a property, not a method, because it is the form 95% of callers want
and C3's ruling was to make the strings one call away from the objects without a
parallel method family.

---

## 6. `ContextCollection` (smart collection, internal) — CHANGED

`flexicon/code/System/context_collection.py`. Two members repaired, no members
added.

| Member | Was | Now |
|---|---|---|
| `boundary_contexts()` | `by_type("PhBoundaryContext")` → always empty | `by_type("PhSimpleContextBdry")` |
| `filter(name_contains=)` | filtered on the garbage `context_name` → never matched | works once `context_name` is repaired |

The second is not an edit to `context_collection.py` at all — `filter` at
`:151` already reads `ctx.context_name` correctly; it is dead only because
`context_name` returns a type name. Fixing `PhonologicalContext.context_name`
repairs it. Recorded here so the repair is not double-counted as a change.

---

## Relationships

```text
PhonologicalDataOA                          (LCM, project-wide pool)
├── PhonRulesOS: IPhSegmentRule
│   ├── PhRegularRule
│   │   ├── StrucDescOS        -> IPhSimpleContext   (read: wrapper.output_specs)
│   │   └── RightHandSidesOS   -> IPhSegRuleRHS  [0..n]
│   │       ├── LeftContextOA  -> IPhPhonContext  -> PhonologicalContext
│   │       ├── RightContextOA -> IPhPhonContext  -> PhonologicalContext
│   │       ├── StrucChangeOS  -> IPhSimpleContext
│   │       ├── InputPOSesRC   -> IPartOfSpeech       (uncast)
│   │       ├── ReqRuleFeatsRC -> IPhPhonRuleFeat -> RuleFeature
│   │       └── ExclRuleFeatsRC-> IPhPhonRuleFeat -> RuleFeature
│   └── PhMetathesisRule
│       └── StrucChange        -> IPhPhonContext   (NO RHS, NO environment)  [C2]
├── ContextsOS: IPhPhonContext                (owned pool; sequence members live here)
│   ├── PhSimpleContextSeg   .FeatureStructureRA -> IPhPhoneme
│   ├── PhSimpleContextNC    .FeatureStructureRA -> IPhNaturalClass
│   │                        .PlusConstrRS / .MinusConstrRS -> IPhFeatureConstraint
│   ├── PhSimpleContextBdry  .FeatureStructureRA -> IPhBdryMarker
│   ├── PhSequenceContext    .MembersRS  -> IPhPhonContext  (references)  [C6]
│   └── PhIterationContext   .Minimum / .Maximum : Int32, .MemberRA  [C5]
└── PhonRuleFeatsOA: CmPossibilityList
    └── PossibilitiesOS: ICmPossibility        (owns the IPhPhonRuleFeats)
        └── IPhPhonRuleFeat  .ItemRA -> IMoInflClass | ICmPossibility  [C4]
```

**Ownership vs reference, the one distinction that bites.** `ContextsOS` and
`PhonRuleFeatsOA.PossibilitiesOS` are *owning* pools — a context created there
belongs to the project. `MembersRS` and the three `*RC` collections are
*reference* collections. Both were confirmed live: `ContextsOS` holds 7 members
in `morphboundary`; `PhonRuleFeatsOA` is a `CmPossibilityList` in all five
projects probed. A writer that adds to a reference collection without adding to
the pool creates a dangling reference; this feature adds no writer, and the two
docstrings that discuss it (C6 `members`, C3 on the RC collections) say so.

---

## State transitions

None. This feature adds one writer — `SetDisabled` (C8) — and it is a plain
boolean assignment on `IPhSegmentRule.Disabled`, with no intermediate state:

```text
Disabled: False <-> True
```

It is bracketed by the class's existing `_TransactionCM` discipline, checked for
`writeEnabled` first, and — per `MorphRuleOperations.SetDisabled`
(`MorphRuleOperations.py:876-880`) — the `hasattr` guard is held *outside* the
transaction bracket so a no-op never opens an empty unit of work. Since
`Disabled` is on the base interface (research.md R-8), there is no guard at all,
and therefore no empty-unit-of-work case.
