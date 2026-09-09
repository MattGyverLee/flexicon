# Live verification -- _GetSequence sweep (follow-up to #277)

**Project:** Target | **Fixture:** target_sandbox (tempdir copy of Target .fwbackup)
**Command:** FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <throwaway probe> -m requires_live_project -q -s
**run_mode:** live (confirmed via tests/live_status.json -> "run_mode": "live")
**Date:** 2026-09-09

## Claim under test

A pattern audit (following the #277 IPhPhonData.EnvironmentsOS fix) flagged six
more _GetSequence overrides that appear to read a nonexistent property on
their guessed parent interface. This is a triage/verification pass only -- no
code was changed. For each site: (1) determine the real parent object from the
class own Create/GetAll/Delete/Duplicate methods, (2) confirm via live .NET
reflection (clr.GetClrType(iface).GetProperties()) against a real LCM whether
the property exists on that real parent, (3) classify.

Probe method: four disposable pytest files under tests/ (deleted after use,
none committed) exercised clr.GetClrType(...).GetProperties() against the six
guessed and corrected interface pairs, then a live call into
DataNotebookOperations.Create() to confirm one derived hypothesis.

## Pre-state / reflection results (read from live LCM via target_sandbox)

```
[FAIL] IWfiWordform.AnalysesOS   near=[HumanApprovedAnalyses, AnalysesOC]
[OK]   IWfiWordform.AnalysesOC
[FAIL] IWfiAnalysis.MorphsOS     near=[MorphBundlesOS]
[OK]   IWfiAnalysis.MorphBundlesOS
[FAIL] IText.ContentsOS          near=[ContentsOA]
[OK]   IText.ContentsOA
[OK]   IStText.ParagraphsOS
[FAIL] IStPara.SegmentsOS        near=[]
[OK]   IStTxtPara.SegmentsOS
[FAIL] IRnGenericRec.RecordsOS   near=[SubRecordsOS]
[OK]   IRnGenericRec.SubRecordsOS
[FAIL] IRnResearchNbkRepository.RecordsOC   near=[]   (runtime type SIL.LCModel.Infrastructure.Impl.RnResearchNbkRepository; own properties = [Singleton, Count])
[FAIL] IPhPhonData.PhonemesOS    near=[PhonemeSetsOS, PhonRuleFeatsOA, PhonRulesOS]
[OK]   IPhPhonemeSet.PhonemesOC
[FAIL] IPhPhonemeSet.PhonemesOS  near=[PhonemesOC]
```

## Action (bonus check, not one of the six)

Called target_sandbox.DataNotebook.Create("TEST_sweep_record", "probe content")
live to confirm a hypothesis raised while tracing the real object graph behind
DataNotebookOperations.

## Post-state (re-queried from LCM)

```
Create raised: AttributeError RnResearchNbkRepository object has no attribute RecordsOC
```

Top-level notebook record creation (DataNotebookOperations.Create()) is
currently broken live -- this is not part of the six _GetSequence sites, it
is a separate defect in Create()/Delete()/Duplicate() discovered while
establishing ground truth for site 5. No object was left behind (Create never
completed; no transaction to roll back). Nothing else in the sandbox was
touched.

## Cleanup

target_sandbox is a disposable tempdir copy; its teardown (in
tests/conftest.py) deleted the sandbox directory after each probe test. No
changes were made to the real Target or Sena 3 projects. All four throwaway
probe files (tests/test_zzz_getsequence_sweep_277b.py through ..._277e.py)
were deleted after use; git status --short tests/ after cleanup shows no
probe files and no stray modifications to files this task did not own.

## Result

[PASS] -- live run confirmed (run_mode: live), all six guessed sites
non-existence was verified live, ground truth for each was re-derived from the
Operations class own Create/GetAll/Delete/Duplicate methods (not just the
original guess), and one additional live-confirmed defect
(DataNotebookOperations top-level record CRUD) was surfaced as a byproduct and
is reported separately below -- not folded into a fix here per the
triage-only mandate.

## Classification table

| # | Site | Real parent (from Create/GetAll/Delete in same file) | Property _GetSequence reads | Exists on real parent? | Correct property | Classification |
|---|------|--------------------------------------------------------|--------------------------------|--------------------------|-------------------|-----------------|
| 1 | WfiAnalysisOperations.py:135 | IWfiWordform (Create: wordform.AnalysesOC.Add(...); GetAll: wordform.AnalysesOC) | AnalysesOS | No | AnalysesOC -- but it is an unordered ILcmOwningCollection (the file own Duplicate() comments at lines 467 and 520 already say so: "AnalysesOC is an unordered ILcmOwningCollection; insert_after has no semantic meaning") | BROKEN-BY-DESIGN |
| 2 | WfiMorphBundleOperations.py:93 | IWfiAnalysis (Create: analysis.MorphBundlesOS.Add(...); GetAll/GetMorphBundles: analysis.MorphBundlesOS; Reorder() in the same file already does Clear/Add on analysis.MorphBundlesOS) | MorphsOS | No | MorphBundlesOS (confirmed ordered -- Duplicate() uses .Insert(index, ...) and .IndexOf(...) on it) | BROKEN-RENAME |
| 3 | TextOperations.py:68 | IText (Create: new_text.ContentsOA = contents, an IStText) | ContentsOS | No | IText.ContentsOA is an atomic reference to an IStText, which owns ParagraphsOS (confirmed IStText.ParagraphsOS exists live) -- there is no direct sequence on IText itself | NEEDS-A-HOP (parent.ContentsOA.ParagraphsOS) |
| 4 | ParagraphOperations.py:61 | IStTxtPara (Create/Delete/Duplicate/GetSegments/GetSegmentCount in the same file all resolve via __GetParagraphObject, which explicitly casts to concrete IStTxtPara -- with a comment at lines 123-131 explaining exactly why: base IStPara "has neither Contents nor SegmentsOS") | SegmentsOS | Yes, on IStTxtPara (confirmed live: IStPara.SegmentsOS fails, IStTxtPara.SegmentsOS exists) | SegmentsOS (no change needed) | FALSE POSITIVE -- the probe guessed the wrong (base) interface; the real parent this class already uses everywhere else is the concrete IStTxtPara, which does have SegmentsOS |
| 5 | DataNotebookOperations.py:127 | IRnGenericRec (CreateSubRecord: parent.SubRecordsOS.Add(...); GetSubRecords: record.SubRecordsOS; Duplicate() sub-record path at lines 2524-2527 uses .IndexOf/.Insert/.Add on SubRecordsOS, with an explicit comment at line 2462 calling it "ordered") | RecordsOS | No | SubRecordsOS | BROKEN-RENAME |
| 6 | PhonemeOperations.py:110 | IPhPhonemeSet (GetAll: phon_data.PhonemeSetsOS[0] then phoneme_set.PhonemesOC; Create: phoneme_set.PhonemesOC.Add(...)) -- not IPhPhonData | PhonemesOS | No (neither on IPhPhonData nor on the real parent IPhPhonemeSet) | PhonemesOC on IPhPhonemeSet -- unordered ILcmOwningCollection, confirmed live (IPhPhonemeSet.PhonemesOS does not exist; only PhonemesOC does) | BROKEN-BY-DESIGN |

## Bonus finding (outside the six sites; reported here because it surfaced while establishing site 5 ground truth)

DataNotebookOperations.Create() (line ~308), Delete() (line ~388), and
Duplicate() (line ~2533) all call repos.RecordsOC where
repos = ServiceLocator.GetService(IRnResearchNbkRepository). Live reflection
shows the repository own runtime type
(SIL.LCModel.Infrastructure.Impl.RnResearchNbkRepository) exposes only
Singleton and Count -- no RecordsOC. A live call to
DataNotebook.Create("TEST_...", ...) against target_sandbox raised
AttributeError: RnResearchNbkRepository object has no attribute RecordsOC
immediately. repos.Singleton returns the actual IRnResearchNbk object, which
live reflection confirms does own RecordsOC (and AllRecords). Top-level
notebook record creation/deletion/duplication is completely non-functional
today -- this is a hard crash on first use, not a silent misbehavior, and is
unrelated to the _GetSequence/reorder pattern this sweep was chartered to
audit. Recommend its own issue (see recommendation below); not fixed here per
the verification/triage-only mandate.

---

# RE-DERIVATION (coordinator pushback): does the sequence contain the reordered item, not does the property exist

**Date:** 2026-09-09 (same session, second pass)
**Fixture:** target_sandbox | **run_mode:** live (re-confirmed via tests/live_status.json)

The property-existence table above answers a necessary but not sufficient
question. The BaseOperations contract is:

    ops.MoveUp(parent_or_hvo, item) -> parent = self._GetObject(parent_or_hvo)
                                     -> sequence = self._GetSequence(parent)
                                     -> locate item inside sequence, move it

so the real question for each site is: when the operations class own
Create/GetAll establish what parent and item mean, does _GetSequence(parent)
return a sequence that actually contains item? Property existence on some
interface is not enough if it is the wrong object property.

This re-derivation traces, for every site, what object each operations class
own Create/GetAll/Delete/Duplicate methods use as parent and what type they
treat as the reordered item, then tests live whether _GetSequence used with
that same parent/item pair works, fails loudly, or (worst case) silently
no-ops.

## Major finding: a systemic one-level shift down the Text -> Paragraph -> Segment chain

Three sites in this family (not just the one originally flagged) all read a
property that belongs to their own child object, one level below where their
own Create/GetAll methods actually operate:

```
IText --(ContentsOA, atomic)--> IStText --(ParagraphsOS)--> IStTxtPara --(SegmentsOS)--> ISegment --(AnalysesRS)--> IAnalysis tokens
```

| Class | Own Create/GetAll item | Own Create/GetAll parent | _GetSequence currently reads | What that property actually belongs to |
|---|---|---|---|---|
| TextOperations | paragraph (via GetParagraphs/GetContents) | IText | ContentsOS (does not exist) | N/A -- GetParagraphs already proves the real fix is ContentsOA.ParagraphsOS |
| ParagraphOperations | paragraph | IText (GetAll/Create take text_or_hvo) | SegmentsOS | IStTxtPara -- the class own CHILD level (segments within a paragraph, which is SegmentOperations job) |
| SegmentOperations | segment (GetAll takes para_or_hvo) | IStTxtPara | AnalysesRS | ISegment -- the class own CHILD level (analyses within a segment) |

ParagraphOperations and SegmentOperations are not independent bugs -- they
are the same shape of defect, one level apart, both pointing one hop too
deep into the own child collection instead of the own level.

## Live confirmation: is the observed failure a silent no-op, or a loud one

Tested directly against target_sandbox (each probe cleaned up after itself;
temporary texts/wordforms/analyses/phonemes were deleted, or in the sandbox
case simply discarded with the sandbox teardown):

```
ParagraphOperations.MoveUp(text, para2)     -> AttributeError: IText object has no attribute SegmentsOS
ParagraphOperations.MoveUp(para1, para2)    -> ValueError: Item not found in sequence
SegmentOperations.MoveUp(para, segs[1])     -> AttributeError: IStTxtPara object has no attribute AnalysesRS
WfiAnalyses.MoveUp(wordform, analysis2)     -> AttributeError: IWfiWordform object has no attribute AnalysesOS
WfiMorphBundles.MoveUp(analysis, bundle2)   -> AttributeError: IWfiAnalysis object has no attribute MorphsOS
Phonemes.MoveUp(phon_data, phoneme2)        -> AttributeError: IPhPhonData object has no attribute PhonemesOS
Phonemes.MoveUp(phoneme_set, phoneme2)      -> AttributeError: IPhPhonemeSet object has no attribute PhonemesOS
```

ParagraphOperations.MoveUp(text, para2) used the parent type that this
operations class own GetAll(text_or_hvo)/Create(text_or_hvo, ...) establish
as the public convention; it raised immediately. MoveUp(para1, para2) used
the level _GetSequence currently (wrongly) assumes -- a paragraph as parent
-- and instead of a silent no-op it raised ValueError: Item not found in
sequence, because para1.SegmentsOS contains segments, never a sibling
paragraph. In every case tested across every site, the failure was a loud
exception (AttributeError or ValueError), never a silent no-op. This
directly answers the most important open question: nobody using any of
these six reorder methods today gets silently-wrong data -- every path that
reaches _GetSequence either crashes outright or raises ValueError on the
item-lookup that follows it.

Two bonus, unrelated findings surfaced while wiring the probes (out of
scope, not fixed, flagged for separate issues):

- DataNotebookOperations.CreateSubRecord() (and, by the same shared private
  helper, likely Delete/GetTitle/every other method that resolves a record
  through __GetRecordObject) calls self.project.project.GetObject(hvo), and
  LcmCache (the live runtime type behind self.project.project) has no
  GetObject method (AttributeError: LcmCache object has no attribute
  GetObject, confirmed live). This is separate from, and in addition to,
  the repos.RecordsOC bug already recorded above for Create() on top-level
  records; this one is in the shared per-record resolver and would also
  break sub-record operations. Not chased further here -- it is orthogonal
  to the _GetSequence question this sweep was chartered to answer, and
  pinning the full blast radius needs its own investigation.

## Reclassification table (this question, not the property-existence question)

| # | Site | Item this class reorders | Real parent (per Create/GetAll) | _GetSequence return value needed | Live-observed failure with current code | Reclassification |
|---|---|---|---|---|---|---|
| 1 | WfiAnalysisOperations.py:135 | IWfiAnalysis | IWfiWordform (unchanged from first pass, same level) | AnalysesOC (unordered) | AttributeError (confirmed live) | BROKEN-BY-DESIGN (unchanged) |
| 2 | WfiMorphBundleOperations.py:93 | IWfiMorphBundle | IWfiAnalysis (unchanged, same level) | MorphBundlesOS (ordered) | AttributeError (confirmed live) | BROKEN-RENAME (unchanged) |
| 3 | TextOperations.py:68 | IStTxtPara (paragraph) | IText (per GetParagraphs/GetContents in the same file, which already do the correct hop) | ContentsOA.ParagraphsOS | not separately re-tested live this pass; site 4 below is the identical shape and was tested | NEEDS-A-HOP (unchanged) |
| 4 | ParagraphOperations.py:61 | IStTxtPara (paragraph) | IText (per GetAll/Create/InsertAt own text_or_hvo convention) | ContentsOA.ParagraphsOS -- identical fix target to site 3 | AttributeError with the conventionally-correct parent; ValueError with the level _GetSequence currently implies (confirmed live, both) | REVISED from FALSE POSITIVE to NEEDS-A-HOP. The property-existence check answered the wrong question: IStTxtPara.SegmentsOS does exist, but it is not this operations class own sequence -- it belongs one level down, to the item SegmentOperations manages. The real defect is that _GetSequence implements SegmentOperations job instead of its own. |
| 5 | DataNotebookOperations.py:127 | IRnGenericRec (sub-record) | IRnGenericRec (the containing record, per CreateSubRecord own parent_record_or_hvo convention; same level, no shift) | SubRecordsOS | not independently re-confirmed live this pass, blocked by the unrelated __GetRecordObject/GetObject bug noted above; structural evidence unchanged from first pass | BROKEN-RENAME (unchanged) |
| 6 | PhonemeOperations.py:110 | IPhPhoneme | IPhPhonemeSet (same level; note Create/GetAll on this class never expose a parent parameter at all, so there is no established public convention for what object a caller would even pass here) | PhonemesOC (unordered) | AttributeError under both plausible parent guesses (confirmed live) | BROKEN-BY-DESIGN (unchanged, plus a note: even the notion of passing a parent is undocumented for this class, since Create/GetAll never take one) |
| extra | SegmentOperations.py:111 | ISegment | IStTxtPara (per this class own GetAll(para_or_hvo) convention) | SegmentsOS (confirmed live to exist on IStTxtPara) | AttributeError: IStTxtPara has no AnalysesRS (confirmed live) | NEW SITE, same family as #4. _GetSequence reads AnalysesRS, which belongs to ISegment (one level down, the reference sequence of interlinear analysis tokens within a single segment), not to the paragraph that owns the sequence of segments. Mechanically a one-line property swap (parent.SegmentsOS), but conceptually the same one-level-down defect as ParagraphOperations, not a plain misspelling like sites 2/5. |

Net effect: three sites (TextOperations, ParagraphOperations,
SegmentOperations) share one underlying defect shape -- each _GetSequence
reaches one level too deep into the own child collection -- rather than
being three unrelated typos. Recommend these three be triaged and fixed
together as a single issue, distinct from the OC/OS BROKEN-BY-DESIGN issues
(sites 1 and 6) and distinct from the plain rename at site 5.
