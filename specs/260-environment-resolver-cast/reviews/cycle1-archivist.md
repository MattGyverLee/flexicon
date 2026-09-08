# Inventory: private object-resolution helpers in flexicon/code/

Scope: every double-underscore Get*Object / Resolve* helper, plus any helper
returning self.project.Object(...) or self.project.project.*GetObject(...).
Started from: grep -rn return self.project.Object( (39 hits), widened to
all def __Get*Object / def __Resolve* (about 90 helpers) and to .GetObject(
call sites (this is how the flexicon#261 candidate was found).

Excluded per instructions: AllomorphOperations.py line 1371,
__GetEnvironmentObject (concurrently being fixed elsewhere; classify only,
not detailed here). It is the third live instance of the uncast
IPhEnvironment defect alongside EnvironmentOperations.py lines 648-659
(flexicon#260, in flight), and would be Class A if it were not already
being handled by another agent.

Call-site counts below are grep -c of the method name in the owning file,
minus the def line itself. Rough per the tasks own allowance, since these
are double-underscore mangled and therefore file-local by construction.

Confidence key:
HIGH = no validation at all, or a documented sibling fix in the same
interface family proves subtype members are read downstream.
MEDIUM = an isinstance / ClassName / hasattr guard rejects the wrong type,
but the correct-type return path is still not re-cast, so whether callers
actually touch a subtype-only member was not individually traced for each
one.
LOW = contract or evidence genuinely ambiguous.

## CLASS D -- wrong or nonexistent lookup API (flexicon#261 class)

| File:line | Helper | Owning class | Docstring promises | Cast behavior | Call sites | Notes |
|---|---|---|---|---|---|---|
| Notebook/DataNotebookOperations.py:182 (def at line 165) | __GetRecordObject | DataNotebookOperations | IRnGenericRec | N/A -- calls nonexistent self.project.project.GetObject(hvo); LcmCache has no such method. The resulting failure is masked as FP_ParameterError, "Invalid notebook record object or HVO" | about 38 | HIGH confidence -- this is flexicon#261 itself, confirmed by the task context and independently re-derived here: a project-wide grep for .GetObject( turns up exactly one other non-ServiceLocator hit, and this is it. |

## CLASS A -- uncast, docstring promises a specific interface (same defect class as #260)

### HIGH confidence (unguarded bare return, or proven by a sibling fix elsewhere)

| File:line | Helper | Owning class | Promised interface | Cast behavior | Call sites | Notes |
|---|---|---|---|---|---|---|
| Lexicon/LexSenseOperations.py:3912 | __GetSenseObject | LexSenseOperations | ILexSense | none | about 79 | Highest call-site count in the whole inventory. |
| Lexicon/ExampleOperations.py:1642 | __GetExampleObject | ExampleOperations | ILexExampleSentence | none | about 24 | |
| TextsWords/WfiMorphBundleOperations.py:1389 | __GetBundleObject | WfiMorphBundleOperations | IWfiMorphBundle | none | about 18 | |
| Grammar/PhonemeOperations.py:1263 | __GetPhonemeObject | PhonemeOperations | IPhPhoneme | none | about 20 | |
| TextsWords/SegmentOperations.py:155 | __GetSegmentObject | SegmentOperations | ISegment | none | about 22 | |
| Lexicon/PronunciationOperations.py:1032 | __GetPronunciationObject | PronunciationOperations | ILexPronunciation | none | about 14 | |
| Grammar/PhonologicalRuleOperations.py:1416 | __ResolveObject | PhonologicalRuleOperations | IPhPhonRule | none, only a wrapper-unwrap step | about 13 | |
| Grammar/NaturalClassOperations.py:106 | __GetNaturalClassObject | NaturalClassOperations | IPhNaturalClass | none | about 13 | Callers duck-type via hasattr(nc, SegmentsRC) at lines 655 and 711 instead of isinstance -- a real silent-loss risk since SegmentsRC and FeaturesOA are subtype-only members. Contradiction found: the docstring of Lexicon/MSAOperations.py __GetMsaObject (around line 1124) claims this helper is a sibling C2 fix site, i.e. already cast. It is not. That claim in MSAOperations.py is stale or false and should be corrected regardless of what happens with this inventory. |
| TextsWords/WfiMorphBundleOperations.py:1451 | __GetMSAObject | WfiMorphBundleOperations | IMoMorphSynAnalysis | none | about 1 | Same interface family (four concrete MSA subtypes) that Lexicon/MSAOperations.py line 1109 __GetMsaObject already fixed with a ClassName cast -- a direct sibling inconsistency inside the same problem domain. |
| Grammar/GramCatOperations.py:584 | __ResolveObject | GramCatOperations | ICmPossibility | none | about 8 | Callers read cat.SubPossibilitiesOS directly (lines 122, 373, 379, 381). SubPossibilitiesOS, Name, and Abbreviation live on ICmPossibility, not ICmObject, so this is a real loss, not a cosmetic one. |
| Lexicon/LexSenseOperations.py:3898 | __GetEntryObject | LexSenseOperations | ILexEntry | none | about 3 | |
| Lexicon/PronunciationOperations.py:1018 | __GetEntryObject | PronunciationOperations | ILexEntry | none | about 3 | |
| Lexicon/AllomorphOperations.py:1308 | __GetEntryObject | AllomorphOperations | ILexEntry | none | about 2 | |
| Lexicon/ExampleOperations.py:1628 | __GetSenseObject | ExampleOperations | ILexSense | none | about 3 | |
| Lexicon/LexSenseOperations.py:3926 | __GetSemanticDomainObject | LexSenseOperations | ICmSemanticDomain | none | about 2 | |
| TextsWords/SegmentOperations.py:141 | __GetParagraphObject | SegmentOperations | IStTxtPara | none | about 5 | |
| TextsWords/WfiMorphBundleOperations.py:1403 | __GetAnalysisObject | WfiMorphBundleOperations | IWfiAnalysis | none | about 3 | |
| TextsWords/WfiMorphBundleOperations.py:1417 | __GetSenseObject | WfiMorphBundleOperations | ILexSense | none | about 1 | |
| Grammar/PhonemeOperations.py:1277 | __GetCodeObject | PhonemeOperations | IPhCode | none | about 1 | |
| Grammar/NaturalClassOperations.py:120 | __GetPhonemeObject | NaturalClassOperations | IPhPhoneme | none | about 2 | |
| TextsWords/WfiMorphBundleOperations.py:1465 | __GetInflectionClassObject | WfiMorphBundleOperations | IMoInflClass | none | about 1 | |
| Grammar/InflectionFeatureOperations.py:1556 | __ResolveInflectionClass | InflectionFeatureOperations | IMoInflClass | none | about 4 | Four near-identical unguarded resolvers in one file (this row plus the next three). |
| Grammar/InflectionFeatureOperations.py:1570 | __ResolveFeatureStructure | InflectionFeatureOperations | IFsFeatStruc | none | about 1 | |
| Grammar/InflectionFeatureOperations.py:1584 | __ResolveFeature | InflectionFeatureOperations | IFsFeatureDefn | none | about 3 | |
| Grammar/InflectionFeatureOperations.py:1598 | __ResolveFeatureSystem | InflectionFeatureOperations | IFsFeatureSystem | none | about 1 | |

### MEDIUM confidence (isinstance / ClassName / hasattr guard rejects the wrong type, but there is no re-cast on the accept path)

| File:line | Helper | Owning class | Promised interface | Cast behavior | Call sites | Notes |
|---|---|---|---|---|---|---|
| Lexicon/LexEntryOperations.py:2433 | __ResolveObject | LexEntryOperations | ILexEntry | isinstance-guarded, no cast | about 54 | |
| TextsWords/WfiAnalysisOperations.py:171 | __GetAnalysisObject | WfiAnalysisOperations | IWfiAnalysis | isinstance-guarded, no cast | about 21 | |
| Notebook/PersonOperations.py:1552 | __ResolveObject | PersonOperations | ICmPerson | isinstance-guarded, no cast | about 28 | |
| Notebook/LocationOperations.py:1651 | __ResolveObject | LocationOperations | ICmLocation | isinstance-guarded, no cast | about 22 | |
| Lexicon/EtymologyOperations.py:1302 | __GetEtymologyObject | EtymologyOperations | ILexEtymology | isinstance-guarded, no cast | about 17 | Elevated priority. CLAUDE.md already documents ILexEtymology as a field-existence trap (its Category 8 note: Source does not exist on ILexEtymology at all). This module is a known fragile spot for exactly this class of same-name or wrong-type confusion. |
| Lexicon/SemanticDomainOperations.py:1312 | __ResolveObject | SemanticDomainOperations | ICmSemanticDomain | isinstance-guarded, no cast | about 16 | |
| Lists/PossibilityListOperations.py:1478 | __ResolveItem | PossibilityListOperations | ICmPossibility | isinstance-guarded, no cast | about 16 | |
| TextsWords/TextOperations.py:84 | __GetTextObject | TextOperations | IText | isinstance-guarded, no cast | about 14 | |
| Lexicon/VariantOperations.py:1115 | __GetVariantObject | VariantOperations | ILexEntryRef | isinstance-guarded, no cast | about 10 | |
| Lists/possibility_item_base.py:118 | __ResolveObject | possibility_item_base, a shared base for several Lists subclasses | ICmPossibility | only an obj-is-None guard, no type check, no cast | about 10 direct, more via subclass inheritance | Shared base class -- the blast radius is likely wider than the direct count, similar in kind to the AllomorphOperations shared-resolver note in the task context. |
| Reversal/ReversalIndexEntryOperations.py:599 | __ResolveObject | ReversalIndexEntryOperations | IReversalIndexEntry | isinstance-guarded, no cast | about 7 | |
| Lexicon/VariantOperations.py:1095 | __GetEntryObject | VariantOperations | ILexEntry | isinstance-guarded, no cast | about 5 | |
| Lexicon/LexReferenceOperations.py:1375 | __ResolveRefType | LexReferenceOperations | ILexRefType | hasattr-guarded, no cast | about 8 | |
| Lists/PossibilityListOperations.py:1458 | __ResolveList | PossibilityListOperations | ICmPossibilityList | isinstance-guarded, no cast | about 6 | |
| Lexicon/LexReferenceOperations.py:1396 | __ResolveLexRef | LexReferenceOperations | ILexReference | hasattr-guarded, no cast | about 5 | |
| Lexicon/LexReferenceOperations.py:1417 | __ResolveSenseOrEntry | LexReferenceOperations | ILexSense or ILexEntry | ClassName-guarded, no cast | about 4 | |
| Lexicon/LexReferenceOperations.py:1439 | __ResolveEntry | LexReferenceOperations | ILexEntry | ClassName-guarded, no cast | about 4 | |
| Reversal/ReversalIndexOperations.py:512 | __ResolveObject | ReversalIndexOperations | IReversalIndex | isinstance-guarded, no cast | about 5 | |
| Reversal/ReversalIndexEntryOperations.py:619 | __GetIndexObject | ReversalIndexEntryOperations | IReversalIndex | isinstance-guarded, no cast | about 3 | |
| Discourse/ConstChartRowOperations.py:532 | __ResolveObject | ConstChartRowOperations | IConstChartRow | isinstance-guarded, no cast | about 7 | |
| Discourse/ConstChartWordGroupOperations.py:483 | __ResolveObject | ConstChartWordGroupOperations | IConstChartWordGroup | isinstance-guarded, no cast | about 7 | |
| Discourse/ConstChartOperations.py:500 | __ResolveObject | ConstChartOperations | IDsConstChart | isinstance-guarded, no cast | about 6 | |
| Discourse/ConstChartRowOperations.py:552 | __ResolveChart | ConstChartRowOperations | IDsConstChart | isinstance-guarded, no cast | about 4 | |
| Discourse/ConstChartWordGroupOperations.py:503 | __ResolveRow | ConstChartWordGroupOperations | IConstChartRow | isinstance-guarded, no cast | about 3 | |
| Discourse/ConstChartMarkerOperations.py:257 | __ResolveMarker | ConstChartMarkerOperations | ICmPossibility | isinstance-guarded, no cast | about 5 | |
| Discourse/ConstChartMovedTextOperations.py:371 | __ResolveObject | ConstChartMovedTextOperations | IConstChartMovedTextMarker | isinstance-guarded, no cast | about 4 | |
| Discourse/ConstChartClauseMarkerOperations.py:390 | __ResolveObject | ConstChartClauseMarkerOperations | IConstChartClauseMarker | isinstance-guarded, no cast | about 4 | |
| Discourse/ConstChartCellTagOperations.py:195 | __ResolveTag | ConstChartCellTagOperations | IConstChartTag | isinstance-guarded, no cast | about 4 | |
| Discourse/ConstChartClauseMarkerOperations.py:410 | __ResolveRow | ConstChartClauseMarkerOperations | IConstChartRow | isinstance-guarded, no cast | about 3 | |
| Discourse/ConstChartCellTagOperations.py:185 | __ResolveRow | ConstChartCellTagOperations | IConstChartRow | isinstance-guarded, no cast | about 3 | |
| Discourse/ConstChartMovedTextOperations.py:391 | __ResolveWordGroup | ConstChartMovedTextOperations | IConstChartWordGroup | isinstance-guarded, no cast | about 2 | |
| Discourse/ConstChartMovedTextOperations.py:411 | __ResolveChart | ConstChartMovedTextOperations | IDsConstChart | isinstance-guarded, no cast | about 1 | |
| Scripture/ScrTxtParaOperations.py:464 | __ResolveObject | ScrTxtParaOperations | IScrTxtPara | isinstance-guarded, no cast | about 5 | |
| Scripture/ScrSectionOperations.py:475 | __ResolveObject | ScrSectionOperations | IScrSection | isinstance-guarded, no cast | about 5 | |
| Scripture/ScrSectionOperations.py:495 | __ResolveBook | ScrSectionOperations | IScrBook | isinstance-guarded, no cast | about 4 | |
| Scripture/ScrNoteOperations.py:571 | __ResolveObject | ScrNoteOperations | IScrScriptureNote | isinstance-guarded, no cast | about 6 | |
| Scripture/ScrBookOperations.py:488 | __ResolveObject | ScrBookOperations | IScrBook | isinstance-guarded, no cast | about 5 | |
| Scripture/ScrTxtParaOperations.py:484 | __ResolveSection | ScrTxtParaOperations | IScrSection | isinstance-guarded, no cast | about 3 | |
| Scripture/ScrDraftOperations.py:389 | __ResolveObject | ScrDraftOperations | IScrDraft | isinstance-guarded, no cast | about 4 | |
| Scripture/ScrNoteOperations.py:591 | __ResolveBook | ScrNoteOperations | IScrBook | isinstance-guarded, no cast | about 3 | |
| Scripture/ScrAnnotationsOperations.py:251 | __ResolveObject | ScrAnnotationsOperations | IScrBookAnnotations | isinstance-guarded, no cast | about 2 | |
| Scripture/ScrAnnotationsOperations.py:271 | __ResolveBook | ScrAnnotationsOperations | IScrBook | isinstance-guarded, no cast | about 2 | |
| Scripture/ScrNoteOperations.py:611 | __ResolveParagraph | ScrNoteOperations | IScrTxtPara | isinstance-guarded, no cast | about 1 | |
| Grammar/StratumOperations.py:91 | __ResolveObject | StratumOperations | no docstring at all -- the class works exclusively with IMoStratum | none | about 5 | LOW-MEDIUM confidence: the interface intent is clear from surrounding code (GetAll and Find both yield IMoStratum), but that itself is an undocumented-contract gap layered on top of the cast gap. |
| TextsWords/WfiMorphBundleOperations.py:1431 | __GetMorphObject | WfiMorphBundleOperations | IMoForm, base of the Stem and Affix allomorph subtypes | none | about 1 | The docstring explicitly disclaims further checking: not type-checked here, SetMorph performs the IMoForm guard after calling this. Looks deliberate, so LOW-MEDIUM confidence this is unintentional. |

## CLASS B -- uncast but the contract only promises a generic or base object (contract-consistent, low priority)

| File:line | Helper | Owning class | Promised return | Why B |
|---|---|---|---|---|
| BaseOperations.py:1674 | _GetObject | BaseOperations, shared, about 10 call sites across subclasses | object | Explicitly generic passthrough helper; every caller casts downstream on its own. |
| BaseOperations.py:2068 | _ResolveFsByGuid | BaseOperations | the resolved LCM object, or None | Generic by design (contract C7 area); never raises, validation is the callers job. |
| BaseOperations.py:2755, used at 2764 and 2766 | __ResolveFeatStrucOperand | BaseOperations | no formal Returns section -- a feature or value operand, deliberately untyped | Internal _MakeFeatStruc plumbing, not a domain object accessor. |
| Grammar/MorphRuleOperations.py:1001 | __ResolveObject | MorphRuleOperations | LCM object, generic, not a named interface | Contract does not promise a specific interface. |
| Grammar/PhonFeatureOperations.py:1063 | __ResolveObject | PhonFeatureOperations | its LCM object, generic | Same reasoning. |
| Grammar/PhonologicalRuleOperations.py:1280 | __ResolveFeature | PhonologicalRuleOperations | its LCM object, generic | Same reasoning. |
| Grammar/PhonologicalRuleOperations.py:1290 | __ResolveLcmObject | PhonologicalRuleOperations | underlying LCM object; the docstring notes it must be identity-preserving for alpha-variable sharing | Deliberately generic; casting here would actively be wrong. |
| Lexicon/MSAOperations.py:1202 | __Resolve | MSAOperations | Generic resolve: HVO becomes object, wrapper becomes unwrapped | Explicitly generic; the domain-specific siblings __ResolveSense and __ResolveEntry layer casts on top of this. |
| TextsWords/SegmentOperations.py:173 | __GetAnalysisObject | SegmentOperations | IAnalysis, the promised type IS the polymorphic base | Contract-consistent: issue #212 was actually fixed downstream, in the consumers that re-cast IAnalysis tokens (WfiAnalysisOperations.__ResolveOwningAnalysis and WfiGlossOperations.__ResolveGloss), both of which already cast (see Class C below). |

## CLASS C -- already casts correctly (confirmed working, no action needed)

| File:line | Helper | Owning class | How it casts |
|---|---|---|---|
| Grammar/POSOperations.py:1107 | __ResolveObject | POSOperations | ClassName == PartOfSpeech leads to IPartOfSpeech(obj) (T7 fix) |
| Lexicon/AllomorphOperations.py:1322 | __GetAllomorphObject | AllomorphOperations | ClassName-dispatched cast to IMoStemAllomorph or IMoAffixAllomorph (T8 defect ii fix) |
| Lexicon/MSAOperations.py:1109 | __GetMsaObject | MSAOperations | ClassName-dispatched cast across four MSA subtypes |
| Lexicon/MSAOperations.py:1190 | __ResolveSense | MSAOperations | unconditional ILexSense(obj) |
| Lexicon/MSAOperations.py:1210 | __ResolveEntry | MSAOperations | ILexEntry(obj), raises FP_ParameterError on failure |
| Notebook/AnthropologyOperations.py:149 | __GetItemObject | AnthropologyOperations | unconditional ICmAnthroItem(obj) |
| System/CheckOperations.py:1163 | __GetCheckObject | CheckOperations | ICmPossibility(obj) on both the int and object branches |
| TextsWords/DiscourseOperations.py:120 | __GetTextObject | DiscourseOperations | IText(self.project.Object(...)) |
| TextsWords/DiscourseOperations.py:149 | __GetChartObject | DiscourseOperations | tries IDsConstChart(obj), falls back to IDsChart(obj) |
| TextsWords/DiscourseOperations.py:190 | __GetRowObject | DiscourseOperations | IConstChartRow(obj) |
| TextsWords/ParagraphOperations.py:77 | __GetTextObject | ParagraphOperations | IText(obj) |
| TextsWords/ParagraphOperations.py:101 | __GetParagraphObject | ParagraphOperations | IStTxtPara(obj) on both the int branch and the object-passthrough branch, the most thorough example in the codebase, with an explicit comment recording the historical bug this fixed |
| TextsWords/WfiAnalysisOperations.py:191 | __ResolveOwningAnalysis | WfiAnalysisOperations | ClassName-dispatch to IWfiAnalysis(obj.Owner) or IWfiAnalysis(obj) (issue #212 fix) |
| TextsWords/WfiGlossOperations.py:88 | __ResolveGloss | WfiGlossOperations | ClassName == WfiGloss guard, then IWfiGloss(gloss) (issue #212 fix) |

## Recommendation (scope decision only, no fixes proposed)

This is not a one-off miss the way #260 and #261 first looked: roughly 55
Class-A helpers span nine modules (Grammar, Lexicon, Lists, Notebook,
Reversal, Scripture, TextsWords, Discourse, System), with call-site counts
as high as about 79 (LexSenseOperations.__GetSenseObject) and about 54
(LexEntryOperations.__ResolveObject). The already-fixed Class-C examples
(POSOperations, AllomorphOperations, MSAOperations, DiscourseOperations,
ParagraphOperations, WfiAnalysisOperations, WfiGlossOperations,
CheckOperations, AnthropologyOperations) prove the fix pattern is well
understood and localized per helper, but sweeps #133 and #176 plus the
T7, T8, and #212 point fixes only reached roughly a third of the affected
sites. The Scripture and Discourse modules in particular are one hundred
percent unfixed and internally consistent with each other, which suggests
neither module was ever touched by any prior sweep. One monolithic issue
would likely stall, being too large to review or land as a single PR;
the recommendation is a per-module set of sweep issues: Scripture,
Discourse, Lexicon (highest call volume, do this one first), the Grammar
remainder, and a combined Reversal, Lists, and Notebook remainder. Each
should be scoped to the guarded-versus-unguarded split above so reviewers
can tell add validation apart from add cast. DataNotebookOperations
(Class D) should stay its own issue, #261, since it is a different bug
shape (wrong API, not a missing cast) and already has a task-context
anchor. The Class-B and Class-C rows need no issue at all.
