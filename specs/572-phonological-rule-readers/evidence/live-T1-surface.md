# Live surface probe -- Issue #572 (phonological rule readers)

**Worktree:** `C:/Github/flexicon-572`, branch `fix/572-phonological-rule-readers`.
**Date:** 2026-09-27
**Nature:** READ-ONLY. Every project opened with `writeEnabled=False`. No factory
was called, no `UndoableOperation` started, nothing written anywhere. Reads are
unrestricted per `CLAUDE.md` / constitution Principle II.

## Exact command

```powershell
cd C:/Github/flexicon-572
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_phonrule_surface_live.py -m requires_live_project -q -s
```

## Result

```
2 passed in 4.43s
```

## LIVE GATE

`tests/live_status.json`, read immediately after the run:

```json
"run_mode": "live"
```

FLEx initialized fully -- FieldWorks 9 at
`C:\Program Files\SIL\FieldWorks 9\`, `SIL.LCModel` loaded, `FLExInitialize()`
completed, 60/60 operations classes loaded. This was a live run, not a mock
fallback.

## Machine-readable artifacts

- `specs/572-phonological-rule-readers/evidence/live-surface-probe.json` --
  reflection of every `SIL.LCModel` type the issue names, off the live runtime
  (properties with declared type / can_read / can_write, methods, interfaces),
  plus the generic-argument types of every collection member.
- `specs/572-phonological-rule-readers/evidence/live-instance-probe.json` --
  real values read off installed projects: rule class names, `Disabled`, the
  `StrucDescOS` and RHS context trees, the `ContextsOS` pool, and the
  `PhonRuleFeatsOA` possibility list.

## Offline baseline (for later comparison)

```powershell
python -m pytest -m "not requires_live_project" -q
# 2575 passed, 1081 deselected, 16 warnings in 18.97s
```

Recorded on the feature branch at `d0a794c` (main), before any change. Any
later delta must be explained, per constitution Principle IV.

## Confirmations

Every property the issue names exists, with these types:

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

## Corrections to the issue text

The issue names two things that do not exist. Both are recorded here so no
part of the design is built on them.

1. **`IPhPhonRuleFeat.FeatureStructureRA` does not exist.**
   `IPhPhonRuleFeat` declares exactly one property, `ItemRA`, and implements
   `ICmPossibility`. There is no `FeatureStructureRA`. Corroborated by
   FieldWorks' own source: `Src/LexText/ParserCore/HCLoader.cs:2610-2623`
   (`LoadMprFeatures`) dispatches on `ruleFeat.ItemRA.ClassID`, and
   `ParserCoreTests/HCLoaderTests.cs:405-411` (`AddPhonRuleFeature`) sets only
   `ItemRA`.

2. **`PhBoundaryContext` / `IPhBoundaryContext` do not exist.** The real
   boundary context is `PhSimpleContextBdry` / `IPhSimpleContextBdry`, with a
   single property `FeatureStructureRA` of type `IPhBdryMarker`. The string
   `PhBoundaryContext` appears nowhere in the FieldWorks source tree
   (`rg -c PhBoundaryContext C:/Github/fieldworks/Src` -> no match, exit 1); it
   appears only in flexicon's own code and docs.

## Live data findings

Five installed projects were opened read-only. Only one holds any phonological
rules.

| Project | Opened | `PhonologicalDataOA` | Rules | `ContextsOS` pool | `PhonRuleFeatsOA` |
|---|---|---|---|---|---|
| Target | yes | yes | 0 | 0 | `CmPossibilityList`, 0 |
| Sena 3 | yes | yes | 0 | 0 | `CmPossibilityList`, 0 |
| Resembli | yes | yes | 0 | 0 | `CmPossibilityList`, 0 |
| Mbugwe Lizzie | yes | yes | 0 | 0 | `CmPossibilityList`, 0 |
| **morphboundary** | yes | yes | **4** | **7** | `CmPossibilityList`, 0 |

`morphboundary`'s four rules (`t deletion`, `a insertion`, `n insertion`,
`n insertion`) are all `PhRegularRule`, and they carry populated data on both
sides of the environment question the issue asks about:

- `t deletion`: `LeftContextOA = None`, `RightContextOA = PhSimpleContextSeg`.
- `a insertion`: `LeftContextOA = PhSimpleContextBdry`,
  `RightContextOA = PhSequenceContext`, `StrucChangeOS` has 1 `PhSimpleContextSeg`.
- `n insertion` (x2): `LeftContextOA = PhSimpleContextSeg` or
  `PhSequenceContext`, `RightContextOA = PhSimpleContextSeg` or
  `PhSequenceContext`.

So: `PhSimpleContextBdry` and `PhSequenceContext` both occur in real data, and
the current `PhonologicalContext.is_boundary_context` check
(`class_type == "PhBoundaryContext"`) matches neither.

Two further facts that shape the tests:

- **No installed project holds an `IPhIterationContext` or an
  `IPhPhonRuleFeat` instance.** `PhonRuleFeatsOA.PossibilitiesOS` is empty in
  all five. Those two readers cannot be verified against pre-existing data on
  this machine; a test must construct the data.
- **Sena 3 opens cleanly and has zero phonological rules.** This contradicts
  `specs/326-phonological-wrapper-members/evidence/live-T1-reflection.md`,
  which recorded Sena 3 as unopenable on 2026-09-22. That earlier finding is
  stale; Sena 3 is readable, and is not a source of phonological data.

## The narrowing trap, measured

pythonnet narrows an object to whatever interface the owning collection yields.
Reading `hasattr` off the raw object is therefore unsound:

| Object, as reached | pythonnet proxy type | `hasattr` result |
|---|---|---|
| `PhonologicalDataOA.PhonRulesOS[i]` | `IPhSegmentRule` | `RightHandSidesOS` -> **False** |
| the same, after `cast_to_concrete` | `IPhRegularRule` | `RightHandSidesOS` -> **True** |
| `rule.StrucDescOS[i]` | `IPhSimpleContext` | `FeatureStructureRA` -> **False** |
| `rhs.LeftContextOA` / `RightContextOA` | `IPhPhonContext` | `FeatureStructureRA` -> **False** |

`IPhSimpleContext` declares **zero** properties, and `IPhPhonContext` declares
only `Name` and `DescriptionOA`. Every context content lives on the concrete
interface. The wrapper base already handles this
(`Shared/wrapper_base.py:149` -- `self._concrete = cast_to_concrete(lcm_obj)`),
so the design rule is: every reader goes through a wrapper or casts explicitly,
and no `hasattr` capability check is ever run against a raw collection element.

## Two dead members this probe exposed

Recorded here, developed in `spec.md` as C7. Both are on the current published
surface and both were measured, not inferred.

- `PhonologicalContext.context_name` does `str(self._concrete.Name)`. `Name` on
  `IPhPhonContext` is an `IMultiString`, so `str()` returns the literal string
  `"SIL.LCModel.DomainImpl.MultiUnicodeAccessor"`. Every live context in
  `morphboundary` returns that same string.
- `PhonologicalContext.description` reads `.Description`. No `IPhPhonContext`
  declares `Description`; the only candidate is `DescriptionOA`, an
  `OwningAtomic` of type `IPhPhonContext`. The property returns `""` for every
  context type.
