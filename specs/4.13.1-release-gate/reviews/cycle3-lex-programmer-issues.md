# Cycle 3 -- new issues from live reflection (Target, read-only)

| # | Title | Label | Type | Failing test |
|---|-------|-------|------|--------------|
| 828 | Pronunciation AddMediaFile/MoveMediaFile add ICmFile to MediaFilesOS | P1 | internal fix | tests/operations/test_issue686_pronunciation_movemedia_hvo_live.py |
| 829 | LexReferenceOperations.GetAll always raises | P1 | internal fix | none dedicated (cycle-2 sweep); new test proposed |
| 830 | Allomorph inflection-class methods on stem allomorphs | P1 | redesign | tests/operations/test_issue740_allomorph_rc_hvo_live.py::test_issue740_remove_inflection_class_after_hvo_refetch |
| 831 | ExampleOperations media methods (no MediaFilesOS) | P1 | redesign | tests/operations/test_issue684_example_movemedia_hvo_live.py |
| 832 | ConstChartClauseMarker dependent clauses need IConstChartRow | P1 | redesign | tests/operations/test_issue752_dependent_clause_hvo_live.py |
| 833 | CheckOperations._GetCheckList stub, no accessor | P2 | fix | tests/operations/test_issue664_check_duplicate_hvo_live.py |
| 834 | NoteOperations.Duplicate insert_after ignored (AnnotationsOC) | P2 | fix/document | tests/operations/test_issue658_note_duplicate_hvo_live.py |

## Reflection evidence
- a (828): ILexPronunciation.MediaFilesOS : ILcmOwningSequence<ICmMedia>; ICmMedia has Label and MediaFileRA : ICmFile. Fix: wrap ICmFile in a new ICmMedia.
- b (830): IMoStemAllomorph has only PhoneEnvRC, StemNameRA. InflectionClassesRC exists on IMoAffixForm (IMoAffixAllomorph inherits it); IMoForm has none. Stem inflection class belongs on the stem MSA.
- c (829): No ReferringLexReferences anywhere. ILexSense.LexSenseReferences and ILexEntry.LexEntryReferences exist (IEnumerable<ILexReference>). Project-wide route: ILexDb.ReferencesOA.PossibilitiesOS -> ILexRefType.MembersOC (Target has 7 types).
- d (831): ILexExampleSentence has no MediaFilesOS (PublishIn, Example, Reference, TranslationsOC, LiftResidue, DoNotPublishInRC).
- e (832): IConstChartClauseMarker.DependentClausesRS : ILcmReferenceSequence<IConstChartRow>.
- 833 label: P2 -- enumeration/delete silently no-op and each GetOrCreate makes an orphan list; narrow area, workaround exists.

## Not filed (contradiction)
- SegmentOperations.__GetSegmentFactory is NOT dead: still called at flexicon/code/TextsWords/SegmentOperations.py:711 (AppendSentence). Only SplitSegment stopped using it. (build/lib copy is stale, ignore.)

## Notes
- Cycle-2 premise file suggested P2 for the #684 follow-up; filed P1 per instruction.
- No library or test code edited.
