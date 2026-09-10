fix(reorder,tsstring): fix _GetSequence ownership/property bugs and IConstChartRow ITsString handling

Fixes three related reorder/read-write bugs against the LCM:

- TextOperations.Sort/MoveUp/MoveDown/MoveToIndex operated against a
  nonexistent ordering of project.lp.Texts (TextsOC, an unordered owning
  collection); the `_GetSequence` override is deleted so the inherited
  NotImplementedError becomes the honest behavior. ParagraphOperations
  and SegmentOperations keep their own `_GetSequence` overrides, each
  matching the single parent type their own Create()/GetAll() already
  require (IText and IStTxtPara respectively) -- the reorder bug reported
  in #299.
- WfiMorphBundleOperations._GetSequence targeted the wrong property name
  on IWfiAnalysis -- the property-rename bug reported in #300.
- ConstChartRowOperations.GetLabel/SetLabel/GetNotes/SetNotes read/wrote
  IConstChartRow.Label/.Notes as IMultiString via the wrong accessor
  shape; IConstChartRow.Label/.Notes are bare ITsString fields -- the
  type-confusion bug reported in #290.

All three fixes are live-LCM verified against target_sandbox; see
specs/299-300-290-reorder-and-tsstring/evidence/live-cycle2.md and
live-cycle2-raw.json for pre/post re-queried field values, and
specs/299-300-290-reorder-and-tsstring/evidence/live-290-reflection.md
for the IConstChartRow live reflection backing the #290 fix.

## Pattern audit

Two sweeps were run against the shapes of all three fixes (repeat-bug
patterns named in CLAUDE.md's Category 8 and the `_GetSequence`
ownership/property-name pattern). Every finding was adjudicated against
the freshly-regenerated LCM contract baseline
(tests/contract/snapshots/liblcm_baseline.json, liblcm 11.0.0.0, generated
2026-09-08T15:18:18Z); full adjudication detail is in
specs/299-300-290-reorder-and-tsstring/evidence/cycle4-snapshot-adjudication.md.

None of the sites below are fixed in this commit. All are follow-up.

### `_GetSequence` ownership/property-name sweep (7 HIGH)

- flexicon/code/TextsWords/WfiAnalysisOperations.py:135 -- HIGH --
  `parent.AnalysesOS`; parent is IWfiWordform, which the snapshot confirms
  has `AnalysesOC` (unordered), not `AnalysesOS`. Verdict: property does
  not exist; remedy is deleting the override, not renaming to `AnalysesOC`
  (OC has no indexer/.MoveTo).
- flexicon/code/TextsWords/DiscourseOperations.py:102 -- HIGH --
  `parent.ChartsOS`; parent is IDsDiscourseData, which the snapshot
  confirms has `ChartsOC`, not `ChartsOS`. Verdict: property does not
  exist; remedy is deletion.
- flexicon/code/Grammar/NaturalClassOperations.py:90 -- HIGH --
  `parent.SubPossibilitiesOS`; parent is IPhNaturalClass, which the
  snapshot confirms has no `Possibilit*` member at all. Verdict: property
  does not exist; remedy is deletion.
- flexicon/code/Grammar/PhonemeOperations.py:110 -- HIGH --
  `parent.PhonemesOS`; parent is IPhPhonemeSet (absent from the snapshot,
  a known extractor coverage gap per #296), but every other method in the
  same file uses `phoneme_set.PhonemesOC` (lines 144, 215, 277, 344, 472,
  1723) -- `PhonemesOS` appears only at lines 108/110, repo-wide. Verdict:
  near-certain nonexistent property; remedy is deletion.
- flexicon/code/Lists/PossibilityListOperations.py:89 -- HIGH --
  `parent.SubPossibilitiesOS` unconditionally, but Create/Delete/Duplicate
  in the same file correctly branch between `SubPossibilitiesOS` (item
  parent, ICmPossibility -- snapshot-confirmed present) and
  `list.PossibilitiesOS` (top-level ICmPossibilityList parent --
  snapshot-confirmed to have `PossibilitiesOS` and no
  `SubPossibilitiesOS`). Verdict: confirmed wrong-property-for-parent-type
  bug for the top-level-list case; needs the same branch the sibling
  methods already have, not deletion.
- flexicon/code/Grammar/InflectionFeatureOperations.py:145 -- HIGH --
  `parent.FeaturesOA.PossibilitiesOS`; snapshot confirms `FeaturesOA`
  resolves to IFsFeatStruc, which has no `PossibilitiesOS` (real child is
  `FeatureSpecsOC`, unordered). Verdict: confirmed broken multi-hop chain,
  contradicting an earlier review record that assumed it was legitimate
  (corrected in reviews/cycle1-domain.md's cycle-5 correction block);
  remedy is deletion (parent collection is unordered).
- flexicon/code/Discourse/ConstChartClauseMarkerOperations.py:447 -- HIGH
  -- `parent.ClauseMarkersOS` (hasattr-guarded); snapshot confirms
  IConstChartRow has `CellsOS`, `Label`, `Notes`, and no `ClauseMarkers`
  member. Verdict: guard is always False; real container is `row.CellsOS`,
  shared with word groups/tags; remedy is deletion or repointing to
  `CellsOS` per class contract.

### Bare-ITsString-as-IMultiString sweep (4 HIGH + 4 MED)

- flexicon/code/Lexicon/LexEntryOperations.py:470 -- HIGH --
  `new_etym.Source.CopyAlternatives(etymology.Source)` on ILexEtymology;
  snapshot confirms ILexEtymology has `LanguageNotes`, no `Source`.
  Verdict: confirmed, will raise AttributeError unconditionally on any
  Duplicate() of an entry with an etymology.
- flexicon/code/Notebook/NoteOperations.py:815-818 (GetAuthor) -- HIGH --
  `note.Source.get_String(ws)` on ICmBaseAnnotation; snapshot confirms
  `SourceRA` only, no bare `Source`. Verdict: confirmed, hasattr guard
  (if any) is False; silently returns "".
- flexicon/code/Notebook/NoteOperations.py:854-858 (SetAuthor) -- HIGH --
  `note.Source.set_String(ws, mkstr)`; same field, snapshot-confirmed
  absent. Verdict: confirmed silent no-op.
- flexicon/code/Notebook/NoteOperations.py:448-449
  (GetSyncableProperties) -- HIGH -- `hasattr(note,"Source")` guard around
  `note.Source.get_String(...)`; snapshot-confirmed `Source` absent on
  ICmBaseAnnotation. Verdict: confirmed, guard always False; author data
  silently omitted from sync export.
- flexicon/code/TextsWords/DiscourseOperations.py:884-888 (SetCellContent,
  Label branch) -- MED -- `hasattr(cell,"Label")` on a chart-cell-part
  object (IConstChartWordGroup/IConstChartTag/IConstChartClauseMarker/
  IConstChartMovedTextMarker from row.CellsOS). Verdict: CONFIRMED DEAD
  BRANCH, not type confusion -- snapshot shows none of the four concrete
  cell-part types expose a `Label` member at all; SetCellContent silently
  no-ops on this branch for every real object it can receive.
- flexicon/code/TextsWords/DiscourseOperations.py:889-893 (SetCellContent,
  Comment branch) -- MED -- same shape for `cell.Comment`. Verdict:
  CONFIRMED DEAD BRANCH -- none of the four cell-part types expose
  `Comment` either.
- flexicon/code/TextsWords/DiscourseOperations.py:948-950 (GetCellContent,
  Label branch) -- MED -- `cell.Label.get_String(...)` inside a
  swallowed-exception try/except. Verdict: CONFIRMED DEAD BRANCH -- masked
  failure returns "" for every real cell-part object rather than a live
  type-confusion crash.
- flexicon/code/TextsWords/DiscourseOperations.py:957-959 (GetCellContent,
  Comment branch) -- MED -- same shape for `cell.Comment`. Verdict:
  CONFIRMED DEAD BRANCH.

None of the 11 HIGH + 4 MED sites above are touched by this commit. All
are tracked as follow-up work.

Closes #299.
Closes #300.
Closes #290.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
