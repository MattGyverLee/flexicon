# Cycle 4 Snapshot Adjudication — reflected-property findings vs. LCM contract baseline

**Date:** 2026-09-10
**Purpose:** Adjudicate every cycle4 pattern-sweep sibling finding
(`reviews/cycle4-sweep-category8.md`, `reviews/cycle4-sweep-getsequence.md`)
against the freshly-regenerated LCM contract baseline, and record the
positive re-validation of the three shipped #299/#300/#290 fixes.

## Snapshot source

- Path: `tests/contract/snapshots/liblcm_baseline.json`
- `liblcm_version`: `11.0.0.0`
- `liblcm_informational_version`: `11.0.0-beta.161+Branch.master.Sha.b87d9f972f472624dfafeabdfd397be3f481436a`
- `generated_at`: `2026-09-08T15:18:18.627100Z`
- Reproduce with:
  ```
  python -c "import json; d=json.load(open('tests/contract/snapshots/liblcm_baseline.json')); print([p for p in d['types']['IWfiWordform']['properties'] if 'Analyses' in p])"
  ```
  which prints `['AnalysesOC', 'HumanApprovedAnalyses']`.

## Reflected-property findings

| LCM interface | Snapshot-confirmed shape |
|---|---|
| `IWfiWordform` | `AnalysesOC` present; **no `AnalysesOS`** |
| `IDsDiscourseData` | `ChartsOC` present; **no `ChartsOS`** |
| `IPhNaturalClass` | **no `Possibilit*` member at all** |
| `ICmPossibilityList` | `PossibilitiesOS` present; **no `SubPossibilities`** |
| `ICmPossibility` | `SubPossibilitiesOS` present |
| `IFsFeatStruc` | `FeatureSpecsOC` present; **no `Possibilit*`** |
| `IConstChartRow` | `CellsOS`, `Label`, `Notes` present; **no `ClauseMarkers`** |
| `ILexEtymology` | `LanguageNotes` present; **no `Source`** |
| `ICmBaseAnnotation` | `SourceRA` only (no bare `Source`) |
| `IConstChartWordGroup` | **no `Label` and no `Comment`** |
| `IConstChartTag` | **no `Label` and no `Comment`** |
| `IConstChartClauseMarker` | **no `Label` and no `Comment`** |
| `IConstChartMovedTextMarker` | **no `Label` and no `Comment`** |

(Exact `IConstChart*` property lists returned by the snapshot for the four
chart-cell-part types are all empty of any `Label`/`Notes`/`Comment`-shaped
member — i.e. the snapshot has zero interesting hits for any of them.)

## Conclusions

**(a) The 4 cycle4 MED `DiscourseOperations` findings are CONFIRMED DEAD
BRANCHES, not type confusion.**

`DiscourseOperations.py:884-888` (`SetCellContent`, Label branch),
`:889-893` (Comment branch), `:948-950` (`GetCellContent`, Label branch),
and `:957-959` (Comment branch) all guard on `hasattr(cell, "Label")` /
`hasattr(cell, "Comment")` where `cell` is one of `IConstChartWordGroup`,
`IConstChartTag`, `IConstChartClauseMarker`, or `IConstChartMovedTextMarker`
(from `row.CellsOS`). The snapshot shows **none** of those four concrete
types expose `Label` or `Comment` at all — not as bare `ITsString`, not as
`IMultiString`, not under any name. The `hasattr` guard is therefore always
`False` for every real object these methods can receive: `SetCellContent`
silently no-ops on those branches, and `GetCellContent` silently returns
`""` via its swallowed-exception fallback. This is not the #290 type-
confusion shape (a field that exists but is the wrong LCM type); it is
dead, unreachable code guarding against a member that was never there.

**(b) `WfiAnalysisOperations.py:135`, `DiscourseOperations.py:102`,
`PhonemeOperations.py:110`, `NaturalClassOperations.py:90` all have
unordered-collection parents, so the correct remedy is deleting the
`_GetSequence` override, not an `OS`→`OC` rename.**

- `WfiAnalysisOperations._GetSequence` → `parent.AnalysesOS`; parent is
  `IWfiWordform`, which the snapshot confirms has `AnalysesOC` (unordered,
  no indexer/`.MoveTo`).
- `DiscourseOperations._GetSequence` → `parent.ChartsOS`; parent is
  `IDsDiscourseData`, which the snapshot confirms has `ChartsOC`.
- `PhonemeOperations._GetSequence` → `parent.PhonemesOS`; parent is
  `IPhPhonemeSet`. `IPhPhonemeSet` is absent from the snapshot (see
  coverage-gap note below), but the same file uses `phoneme_set.PhonemesOC`
  consistently at lines 144, 215, 277, 344, 472, and 1723 — `PhonemesOS`
  appears **only** at lines 108 and 110, repo-wide.
- `NaturalClassOperations._GetSequence` → `parent.SubPossibilitiesOS`;
  parent is `IPhNaturalClass`, which the snapshot confirms has **no**
  `Possibilit*` member of any kind — `IPhNaturalClass` is not
  `CmPossibility`-hierarchical, so there is no sequence of any name to
  reorder.

In every one of these four cases, `OS`→`OC` renaming the target property
would not fix the bug: the parent's actual child collection is an unordered
`ObjectCollection` (or, for `IPhNaturalClass`, does not exist at all), and
`BaseOperations.Sort/MoveUp/MoveDown/MoveToIndex` require an indexer and
`.MoveTo()` that `OC`-family collections do not provide. The correct fix is
to delete the `_GetSequence` override entirely so the inherited
`BaseOperations._GetSequence` `NotImplementedError` becomes the honest
behavior — this generalizes the `TextOperations` ruling already made in
`reviews/cycle1-domain.md` Q1 (`project.lp.Texts` is `TextsOC`; the fix was
deletion, not renaming to a nonexistent `TextsOS`/`TextsOC`-with-indexer
hybrid), and matches the existing no-override precedent in
`LexEntryOperations.py`.

## `PhonemeOperations.py:110` coverage note

`IPhPhonemeSet` is absent from the snapshot entirely (see gap note below),
so the adjudication above for `PhonemeOperations.py:110` rests on
source-internal consistency rather than a direct reflected hit: `PhonemesOS`
appears **only** at lines 108 and 110 in `PhonemeOperations.py` (both inside
the `_GetSequence` override itself), while every other method in the same
file — `Create`, `Delete`, `Duplicate`, `GetAll`, and others — uses
`phoneme_set.PhonemesOC` at lines 144, 215, 277, 344, 472, and 1723. The
`_GetSequence` override is the sole outlier in its own file.

## Snapshot coverage gap (issue #296)

Three types referenced by cycle4 findings are absent from the baseline
snapshot: `IPhPhonemeSet`, `IConstituentChartCellPart`, and
`IFsFeatureSystem`. This is a known extractor limitation (issue #296): the
extractor only tracks literal `TypeName.member` access patterns found in
source, so interfaces that are never accessed by that literal shape
anywhere in the codebase do not appear, even though they are real LCM
types. This gap does not undermine the findings above — `IPhNaturalClass`,
`IWfiWordform`, `IDsDiscourseData`, `IConstChartRow`, and the four
`IConstChart*` chart-cell-part types are all present and directly
reflected in the snapshot.

## Positive re-validation of the shipped fixes

- `IText.ContentsOA` exists; `IText` has **no** `ParagraphsOS` — confirms
  `ParagraphOperations._GetSequence`'s `parent.ContentsOA.ParagraphsOS`
  chain resolves through the correct intervening object for its documented
  `IText` parent type.
- `IStText.ParagraphsOS` — confirmed present (the collection
  `ParagraphOperations._GetSequence` actually returns, one hop past
  `ContentsOA`).
- `IStTxtPara.SegmentsOS` — confirmed present, matching
  `SegmentOperations._GetSequence`'s `parent.SegmentsOS`.
- `IWfiAnalysis.MorphBundlesOS` — confirmed present, matching
  `WfiMorphBundleOperations`'s reordering target.

All four shipped-fix target properties are snapshot-confirmed to exist
exactly as implemented; none of the cycle4 adjudication above touches or
contradicts the shipped code.
