# #284 Re-triage: uncast resolvers on the caller-usage axis

**Status:** complete  
**Anchor commit:** `e1e47f8` (`origin/main`, 2026-09-25 — post-#282 and post the #455–#489 promotion wave)  
**Tracking issue:** https://github.com/MattGyverLee/flexicon/issues/284

## Method

Per helper that still returns `project.Object(...)` without a cast, answer:

> Does at least one caller perform Python attribute access (or `hasattr` /
> `getattr`) on the resolved object for a member that is **not** on
> `ICmObject`?

- **Yes → behavioural.** Rank `hasattr`-gated silent-loss first. Evidence
  cites caller `file:line` + member name.
- **No → contract-only.** Batch into one housekeeping issue. No live gate.

Inventory taken by scanning every `__Get*Object` / `__Resolve*` that
touches `project.Object` / `.GetObject(`, classifying cast presence
(`cast_to_concrete`, `return IXxx(...)`, ClassName-dispatch tables), then
walking same-file callers for attribute use. Deliberate Class-B generics
(docstring promises no specific interface) stay contract-only even when
uncast.

## Headline numbers (against the ~55 warning)

| Bucket | Count |
|--------|------:|
| Resolvers scanned | 96 |
| Already cast (skip) | 84 |
| Still uncast + `Object` lookup | 12 |
| → behavioural | **7** |
| → contract-only | **5** |

The original ~55 Class-A figure counted contract mismatches, not defects.
After post-#282 casts and the #455–#489 promotion wave, the behavioural
remainder is **seven helpers in three modules**.

## (a) Ranked behavioural-defect list

Rank: `hasattr`-silent first, then direct attribute access. Each row is
one helper; evidence is representative, not exhaustive.

### Rank 1 — `hasattr`-gated silent loss

| # | Helper | Evidence | Issue |
|---|--------|----------|-------|
| 1 | `Lists/PossibilityListOperations.py:1539` `__ResolveItem` → `ICmPossibility` | `:793` `hasattr(poss_item, "Description")`; `:790`/`:791`/`:794` read `Name` / `Abbreviation` / `Description`; `:590` `parent_obj.SubPossibilitiesOS.Add(...)`; `:960`/`:1000`/`:1032` name/abbr getters/setters | **#492** (Lists sweep) |
| 2 | `Grammar/PhonFeatureOperations.py:1088` `__ResolveObject` | `:201`/`:425` `hasattr(..., "Description")`; `:175`/`:188`/`:203` `Name` / `Abbreviation` / `Description`; `:222` `feature.ValuesOC` | **#490** (already open) |

### Rank 2 — direct attribute access (`AttributeError` on HVO)

| # | Helper | Evidence | Issue |
|---|--------|----------|-------|
| 3 | `Lists/PossibilityListOperations.py:1519` `__ResolveList` → `ICmPossibilityList` | `:423`/`:466` `poss_list.Name`; `:509`/`:512`/`:592` `PossibilitiesOS` | **#492** |
| 4 | `Scripture/ScrSectionOperations.py:506` `__ResolveBook` → `IScrBook` | `:132`/`:221`/`:224`/`:264`/`:453`–`:463` `book.SectionsOS` | **#493** (Scripture sweep) |
| 5 | `Scripture/ScrTxtParaOperations.py:494` `__ResolveSection` → `IScrSection` | `:133`/`:137`/`:149`/`:240`/`:244`/`:247`/`:284`/`:287` `section.ContentOA` | **#493** |
| 6 | `Scripture/ScrNoteOperations.py:601` `__ResolveBook` → `IScrBook` | `:149`/`:154`/`:156`/`:281`/`:284`/`:330`/`:333` `book.FootnotesOS` | **#493** |
| 7 | `Scripture/ScrAnnotationsOperations.py:281` `__ResolveBook` → `IScrBook` | `:119`/`:128`/`:207`/`:208` `book.FootnotesOS` | **#493** |

### Already repaired from the original #284 promotions

These were the two rows #284 marked promotable on caller evidence at filing
time; both are now cast on `main`:

| Original promotion | Disposition |
|--------------------|-------------|
| `GramCatOperations.__ResolveObject` (callers read `SubPossibilitiesOS`) | Class deleted as a CRUD surface (#276); thin deprecated alias of `POSOperations`, whose `__ResolveObject` casts |
| `NaturalClassOperations.__GetNaturalClassObject` (`hasattr(nc, "SegmentsRC")`) | Casts via `cast_to_concrete` (landed with the NaturalClass / #483 family) |

Promoted-and-closed during the re-triage window (caller evidence in each
issue body): #455, #457, #459, #461, #463, #465, #481, #483, #486, #488.
Still open from that wave: **#490**.

## (b) Contract-only housekeeping

One issue: **#494**. No live gate, no module split. Scope is docstring /
eager-cast hygiene only — do **not** cast deliberate generics.

| Helper | Why contract-only |
|--------|-------------------|
| `BaseOperations.py:2949` `__ResolveFeatStrucOperand` | Polymorphic operand resolver (HVO / GUID / name / object); casting here would be wrong |
| `Grammar/PhonologicalRuleOperations.py:1285` `__ResolveFeature` | Docstring promises generic LCM object |
| `Grammar/PhonologicalRuleOperations.py:1295` `__ResolveLcmObject` | Identity-preserving by design (alpha-variable sharing); casting would be actively wrong |
| `Scripture/ScrNoteOperations.py:621` `__ResolveParagraph` | Sole caller (`Create` `:145`) binds the result and never touches a subtype member |
| `TextsWords/SegmentOperations.py:181` `__GetAnalysisObject` | Promises polymorphic `IAnalysis` base; consumers re-cast (#212) |

## Out of scope (unchanged)

- `DataNotebookOperations.__GetRecordObject` / wrong lookup API → #261 class
  (different bug shape). Now casts after later work; not part of this axis.
- Collection-element casts → covered by #270 / `cast_all` /
  `_GetTypedElements`, absent from the original resolver inventory.

## Remedy (for the behavioural issues)

Route every return path through public `cast_to_concrete` (or the
appropriate concrete interface), matching #269: guard on the **union** of
`isinstance` and `ClassName` so a ClassName-only guard is not narrower
than existing behaviour for subclasses absent from the cast registry.
Each behavioural issue needs a RED-first live gate before the fix.
