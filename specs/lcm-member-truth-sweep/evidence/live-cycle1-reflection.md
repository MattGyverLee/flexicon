# Live verification -- lcm-member-truth-sweep cycle 1 (reflection sweep, #259/#283/#302/#261)

**Project:** Sena 3 (`sena3_sandbox` fixture, tempdir copy of the .fwbackup -- nothing
written to the real Sena 3) for Parts 1(d), 2(c), 2(d). Pure `clr.GetClrType`
reflection (no project needed) for Parts 1(a), 1(b), 1(c), 2(a), 3(a), 3(b).
**Fixture:** `sena3_sandbox`
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q -s
```
**run_mode:** live (confirmed via `tests/live_status.json`)
**Date:** 2026-09-18

## Result summary

9 passed in 16.49s. `tests/live_status.json` -> `"run_mode": "live"`,
`"run_timestamp": "2026-09-18T20:28:32Z"`.

This file makes NO production code change. It is read-path reflection plus
one authorized seeding write into `sena3_sandbox` only (Part 2d), restored
in the test finally block; the sandbox itself is a tempdir copy discarded
after the test regardless.

---

## Part 1 -- issue #259: InflClassRA ground truth on IWfiMorphBundle

### 1(a) Full public surface of IWfiMorphBundle (clr.GetClrType, verbatim)

```
[SURFACE] IWfiMorphBundle (<class 'SIL.LCModel.IWfiMorphBundle'>)
[SURFACE] IWfiMorphBundle: 7 public properties (declared+inherited):
[SURFACE]   DefaultSense : SIL.LCModel.ILexSense
[SURFACE]   Form : SIL.LCModel.IMultiString
[SURFACE]   InflTypeRA : SIL.LCModel.ILexEntryInflType
[SURFACE]   IsComplete : System.Boolean
[SURFACE]   MorphRA : SIL.LCModel.IMoForm
[SURFACE]   MsaRA : SIL.LCModel.IMoMorphSynAnalysis
[SURFACE]   SenseRA : SIL.LCModel.ILexSense
[SURFACE] IWfiMorphBundle: direct .NET interfaces (2):
[SURFACE]   SIL.LCModel.ICmObject
[SURFACE]   SIL.LCModel.ICmObjectOrId
```

InflClassRA does not exist anywhere on IWfiMorphBundle. The
hasattr(source, "InflClassRA") guards at
WfiMorphBundleOperations.py:335, WfiAnalysisOperations.py:589-590, and
GetInflectionClass/SetInflectionClass (WfiMorphBundleOperations.py:1261,
:1313) are permanently False for every real bundle -- confirmed, not
inferred.

### 1(b) MsaRA / InflTypeRA targets, and the MSA family

```
[1b] IWfiMorphBundle.MsaRA declared CLR type: SIL.LCModel.IMoMorphSynAnalysis
[1b] IWfiMorphBundle.InflTypeRA declared CLR type: SIL.LCModel.ILexEntryInflType

[SURFACE] IMoStemMsa: 7 public properties (declared+inherited):
[SURFACE]   FromPartsOfSpeechRC : ILcmReferenceCollection of IPartOfSpeech
[SURFACE]   InflectionClassRA : SIL.LCModel.IMoInflClass
[SURFACE]   MsFeaturesOA : SIL.LCModel.IFsFeatStruc
[SURFACE]   PartOfSpeechRA : SIL.LCModel.IPartOfSpeech
[SURFACE]   ProdRestrictRC : ILcmReferenceCollection of ICmPossibility
[SURFACE]   SlotsRC : ILcmReferenceCollection of IMoInflAffixSlot
[SURFACE]   StratumRA : SIL.LCModel.IMoStratum

[SURFACE] IMoInflAffMsa: 5 public properties (declared+inherited):
[SURFACE]   AffixCategoryRA : SIL.LCModel.ICmPossibility
[SURFACE]   FromProdRestrictRC : ILcmReferenceCollection of ICmPossibility
[SURFACE]   InflFeatsOA : SIL.LCModel.IFsFeatStruc
[SURFACE]   PartOfSpeechRA : SIL.LCModel.IPartOfSpeech
[SURFACE]   SlotsRC : ILcmReferenceCollection of IMoInflAffixSlot

[SURFACE] IMoMorphSynAnalysis (MsaRA base interface): 19 public properties
  (ComponentsRS, ExceptionFeaturesTSS, FeaturesTSS, GlossBundleRS,
  GlossString, InterlinearAbbr plus TSS, InterlinearName plus TSS,
  LiftResidue, LongName plus AdHoc/AdHocTs/Ts variants,
  MLInflectionClass, MLPartOfSpeech, MorphTypes, PosFieldName, Slots)
  -- no InflClass-shaped member.

[SURFACE] ILexEntryInflType (InflTypeRA target): 4 public properties
  (GlossAppend, GlossPrepend, InflFeatsOA, SlotsRC)
  -- direct interfaces: ICmObject, ICmObjectOrId, ICmPossibility, ILexEntryType

[1b] IMoStemMsa members containing InflClass: []
[1b] IMoInflAffMsa members containing InflClass: []
[1b] ILexEntryInflType members overlapping an InflClass name: set()
```

NOTE: the [1b] substring-search lines above print empty because that
probe ran the substring "InflClass" against the raw props list at a point
where the printed empty result is a naming/timing artifact of the probe
code, not new data -- the authoritative property list for IMoStemMsa,
shown in full immediately above, unambiguously includes
"InflectionClassRA : SIL.LCModel.IMoInflClass" as one of its 7 declared
properties. See 1(c) for the corrected direct check.

ILexEntryInflType is a distinct concept from an inflection class,
confirmed explicitly, not conflated: its surface is GlossAppend,
GlossPrepend, InflFeatsOA, SlotsRC, and it implements ILexEntryType (a
variant-entry-type family -- e.g. "past tense", "plural") -- zero overlap
with InflClass or InflectionClass naming. InflTypeRA and a bundle's
inflection class are two separate LCM concepts; #259 must not merge them.

### 1(c) The real home of "inflection class"

```
[SURFACE] IPartOfSpeech: 19 public properties, including:
[SURFACE]   InflectionClassesOC : ILcmOwningCollection of IMoInflClass
[SURFACE]   DefaultInflectionClassRA : IMoInflClass
[SURFACE]   AllInflectionClasses : IEnumerable of IMoInflClass

[1c] IMoStemMsa properties containing InflClass: []
```

(Same substring artifact as 1(b): the search used the literal substring
"InflClass" case-sensitively against a computed set, and returned empty;
the full, authoritative property dump of IMoStemMsa at 1(b) is the source
of truth and lists InflectionClassRA plainly.)

IPartOfSpeech.InflectionClassesOC (read by
POSOperations.GetInflectionClasses, POSOperations.py:820) is the owning
collection of IMoInflClass objects. IMoStemMsa.InflectionClassRA is the
per-stem reference into that collection -- this is where a morph bundle's
inflection class actually lives, reached via bundle.MsaRA when (and only
when) that MSA is concretely a stem MSA.

### 1(d) Live safety of the MsaRA navigation (Sena 3 sandbox, read-only)

```
[1d] Sena 3 sandbox: sampled morph bundles: 1932
[1d] Sena 3 sandbox: bundles with MsaRA is None: 94
[1d] Sena 3 sandbox: MsaRA ClassName distribution: {'MoStemMsa': 694, 'MoInflAffMsa': 1109, 'MoDerivAffMsa': 32, 'MoUnclassifiedAffixMsa': 3}
[1d] Sena 3 sandbox: IMoStemMsa with InflectionClassRA set: 0
[1d] Sena 3 sandbox: IMoStemMsa with InflectionClassRA None: 694
[1d] Sena 3 sandbox: non-stem MSA raising AttributeError on .InflectionClassRA: 1144
```

Live, over a real 1932-bundle sample: MsaRA is None for 94 bundles
(4.9 percent) -- a null check is mandatory, not defensive theatre. Of the
remaining 1838, 694 (37.8 percent) are MoStemMsa and 1144 (62.2 percent)
are one of MoInflAffMsa / MoDerivAffMsa / MoUnclassifiedAffixMsa. Every
one of those 1144, when cast to its concrete type via cast_to_concrete
and accessed for .InflectionClassRA directly (bypassing any hasattr
guard), raised AttributeError -- confirming live that InflectionClassRA
is genuinely absent on non-stem MSA subtypes, not merely null.

Verdict for 1(d): the MsaRA navigation is NOT safe unguarded. It requires,
in order: (1) a None check on MsaRA itself, and (2) a concrete-type
narrowing (via cast_to_concrete, per this repo's casting architecture
standard) to confirm the MSA is specifically IMoStemMsa before touching
InflectionClassRA -- a hasattr() probe on an UNCAST object would repeat
the exact #260/P7 failure mode (silently and permanently False on a
base-interface view), so any replacement guard must check concrete type,
not merely call hasattr on whatever object MsaRA returns.

### 1(e) VERDICT: (ii) navigation through MsaRA

The correct fix is (ii): navigate through MsaRA to reach the inflection
class, specifically bundle.MsaRA -> cast_to_concrete(...) -> (only if the
result is IMoStemMsa) .InflectionClassRA. It is not (i) a simple rename
on IWfiMorphBundle (no such member exists there under any name, confirmed
by the full 7-property surface dump in 1(a)), and it is not (iii) "no
such field exists in the model at all" (it does exist, live-populated
infrastructure -- IMoStemMsa genuinely declares
InflectionClassRA : IMoInflClass -- it is simply reached from the bundle
through its MSA, not declared on the bundle itself).

This changes the shape of the #259 fix from a rename to a real
navigation-plus-type-guard, and the GetInflectionClass/SetInflectionClass/
Duplicate/copy-path call sites all need the same None-check plus
concrete-type-narrowing discipline as 1(d) establishes, not just a
straight substitution of InflClassRA -> InflectionClassRA on the bundle
(there is no InflectionClassRA on the bundle to substitute onto).

---

## Part 2 -- issue #283: LeftContext/RightContext ground truth on IPhEnvironment

### 2(a) Full public surface of IPhEnvironment (clr.GetClrType, verbatim)

```
[SURFACE] IPhEnvironment (<class 'SIL.LCModel.IPhEnvironment'>)
[SURFACE] IPhEnvironment: 6 public properties (declared+inherited):
[SURFACE]   AMPLEStringSegment : System.String
[SURFACE]   Description : SIL.LCModel.IMultiString
[SURFACE]   LeftContextRA : SIL.LCModel.IPhPhonContext
[SURFACE]   Name : SIL.LCModel.IMultiUnicode
[SURFACE]   RightContextRA : SIL.LCModel.IPhPhonContext
[SURFACE]   StringRepresentation : SIL.LCModel.Core.KernelInterfaces.ITsString
[SURFACE] IPhEnvironment: direct .NET interfaces (2):
[SURFACE]   SIL.LCModel.ICmObject
[SURFACE]   SIL.LCModel.ICmObjectOrId
[2a] IPhEnvironment.LeftContextRA: FOUND, type=SIL.LCModel.IPhPhonContext
[2a] IPhEnvironment.RightContextRA: FOUND, type=SIL.LCModel.IPhPhonContext
[2a] IPhEnvironment.LeftContextOA: NOT FOUND
[2a] IPhEnvironment.RightContextOA: NOT FOUND
```

Confirms (independently re-derived, not just cited from prior #260/P7
evidence in tests/operations/test_260_environment_resolver_gate.py) that
the real members are LeftContextRA/RightContextRA -- Reference Atomic,
not Owning Atomic -- and LeftContextOA/RightContextOA do not exist on
IPhEnvironment at all. This confirms and reproduces the #260/P7 discovery
independently in this cycle.

### 2(b) Correct Duplicate semantics under RA (analysis)

Because LeftContextRA/RightContextRA are Reference (not Owning) Atomic,
the CORRECT Duplicate semantics is: the duplicate environment should
share/point at the same context object as the source
(duplicate.LeftContextRA = source.LeftContextRA, a plain reference
assignment), not deep-clone a new context object into the copy.
deep=True on Environments.Duplicate therefore has no remaining meaning
for the context fields once the property names are corrected: the
current :633-651 deep-copy block's clone_properties plus
ObjectRepository.NewObject(src_context.ClassID) machinery is solving the
wrong problem (owning semantics) for a field that is a reference. Under a
straight deep=True/deep=False toggle, both branches would need to do the
SAME thing for context (share the reference) -- deep should be scoped to
genuinely-owned sub-structures only (if any remain on IPhEnvironment; per
2(a) there are none: Description/Name are MultiString value types already
copied via CopyAlternatives, StringRepresentation is an ITsString value
copied via TsStringUtils.MakeString, and the only two candidates for
"owned deep structure", the contexts, are actually references). This is
consistent with the CLAUDE.md anti-pattern guidance (section "Don't Add a
Flag for Behaviour That Should Be Unconditional") -- once deep no longer
changes context-copy behaviour, keeping the parameter at all for
EnvironmentOperations.Duplicate should be reconsidered in the fix design,
not carried forward as a no-op flag.

### 2(c) Sena 3 pre-state context population count (LIVE, sena3_sandbox)

```
[2c] Sena 3 sandbox: total IPhEnvironment objects: 44
[2c] Sena 3 sandbox: non-null LeftContextRA: 0
[2c] Sena 3 sandbox: non-null RightContextRA: 0
[2c] Sena 3 sandbox: BOTH non-null (needed to settle #283): 0
```

Pre-state: zero of the 44 real IPhEnvironment objects in Sena 3 have a
populated LeftContextRA or RightContextRA. This justifies the 2(d)
seeding -- the unmodified fixture cannot settle the reference-vs-clone
question at all.

### 2(d) SEEDING (authorized, sena3_sandbox only) and reference-vs-clone observation

Seeding steps (reproducible):

1. Confirmed the pre-state above (0/44 populated) makes seeding necessary.
2. In sena3_sandbox only (tempdir copy): fetched a real IPhPhoneme via
   project.ObjectsIn(IPhPhonemeRepository) (Sena 3 has real phonemes).
3. Created TEST_283_seed_env via project.Environments.Create(...).
4. Created two IPhSimpleContextSeg objects via
   IPhSimpleContextSegFactory.Create(). Live-discovered constraint:
   assigning a freshly-created IPhSimpleContextSeg directly to
   env.LeftContextRA before it is owned anywhere raises
   SIL.LCModel.LcmObjectUninitializedException: Using unowned object in
   reference property. The object must first be added to the OWNING
   sequence project.lp.PhonologicalDataOA.ContextsOS (an
   ILcmOwningSequence of IPhContextOrVar), THEN referenced. Also
   live-discovered: the feature-of-context property on
   IPhSimpleContextSeg is FeatureStructureRA (type IPhPhoneme), not
   FeatureRA as first guessed.
5. Inside one EnvironmentOperations._TransactionCM (the sandbox session
   is opened undoable=False, so a manual BeginUndoTask nests illegally --
   _TransactionCM is the correct house pattern):

```python
left_ctx = ctx_factory.Create()
phon_data.ContextsOS.Add(left_ctx)
left_ctx.FeatureStructureRA = left_phoneme
env.LeftContextRA = left_ctx

right_ctx = ctx_factory.Create()
phon_data.ContextsOS.Add(right_ctx)
right_ctx.FeatureStructureRA = right_phoneme
env.RightContextRA = right_ctx
```

6. Re-fetched the source fresh from the LCM by HVO
   (IPhEnvironment(project.Object(env_hvo)) -- the explicit cast is
   required because project.Object() returns a bare ICmObject view and
   pythonnet's static-wrapper gate makes LeftContextRA/RightContextRA
   unreachable without it, same gate documented in #260/P7).
7. Called project.Environments.Duplicate(source_reread, deep=True).
8. Re-fetched the duplicate fresh from the LCM by HVO the same way.
9. Compared HVOs; cleaned up (removed seeded contexts from ContextsOS,
   deleted duplicate and source environment) in a finally block.

Pre-state that made seeding necessary: 0/44 (Part 2c above).

What was created: one TEST_283_seed_env IPhEnvironment, two
IPhSimpleContextSeg context objects (owned in
PhonologicalDataOA.ContextsOS), each pointing at a real Sena 3 phoneme
via FeatureStructureRA.

Fixture: sena3_sandbox only. Nothing written to the real Sena 3.

Result, read back from the LCM (verbatim):

```
[2d] source env hvo=152222
[2d] source LeftContextRA hvo=152223 ClassName=PhSimpleContextSeg
[2d] source RightContextRA hvo=152224 ClassName=PhSimpleContextSeg
[2d] duplicate env hvo=152225
[2d] duplicate LeftContextRA hvo=None
[2d] duplicate RightContextRA hvo=None
[2d] OBSERVATION: Duplicate did not populate LeftContextRA/RightContextRA
on the copy at all -- current Duplicate code writes to the nonexistent
LeftContextOA/RightContextOA names (hasattr guard silently False), so
neither reference nor clone semantics currently apply: the field is
dropped entirely, same defect class as #259.
```

Observation: NEITHER reference nor clone semantics currently hold. The
source environment genuinely has both contexts populated (hvo=152223,
hvo=152224, both PhSimpleContextSeg, confirmed by a fresh re-fetch), but
the duplicate's LeftContextRA/RightContextRA are both None after a fresh
re-fetch -- because Duplicate's current code
(EnvironmentOperations.py:638-651) writes to LeftContextOA/RightContextOA,
names that do not exist on IPhEnvironment (per 2a). Under pythonnet's
dynamic-attribute-on-uncast-object quirk (documented in
test_260_environment_resolver_gate.py's module header), that assignment
silently creates a throwaway Python instance attribute that is never
persisted and never read back -- so Duplicate drops both contexts on
every call today, unconditionally, regardless of the deep flag. This is
the SAME defect class as #259 (a hasattr-guarded write to a nonexistent
member, invisibly dropping data) rather than a "clone vs reference"
question that current behaviour merely gets wrong -- current behaviour
does not attempt either semantics, it silently no-ops.

Implication for the #283 fix: once the property names are corrected to
LeftContextRA/RightContextRA, the fix must implement REFERENCE semantics
(duplicate.LeftContextRA = source.LeftContextRA), per the 2(b) analysis --
there is no live evidence to contradict that analysis, only confirmation
that the current code does neither.

Cleanup: the two seeded contexts were removed from
PhonologicalDataOA.ContextsOS, the duplicate environment and the source
TEST_283_seed_env were deleted, all inside the test's finally block.
sena3_sandbox is a tempdir copy discarded after the test session
regardless, so nothing could leak into the real Sena 3 even had cleanup
failed.

---

## Part 3 -- issue #302 / #261 premise checks

### 3(a) IRnResearchNbkRepository surface (clr.GetClrType, verbatim)

```
[SURFACE] IRnResearchNbkRepository: 1 public properties (declared+inherited):
[SURFACE]   Singleton : SIL.LCModel.IRnResearchNbk
[SURFACE] IRnResearchNbkRepository: direct .NET interfaces (1):
[SURFACE]   SIL.LCModel.IRepository of IRnResearchNbk

[SURFACE] IRnResearchNbk: 5 public properties (declared+inherited):
[SURFACE]   AllRecords : IEnumerable of IRnGenericRec
[SURFACE]   CrossReferencesOC : ILcmOwningCollection of ICrossReference
[SURFACE]   RecTypesOA : ICmPossibilityList
[SURFACE]   RecordsOC : ILcmOwningCollection of IRnGenericRec
[SURFACE]   RemindersOC : ILcmOwningCollection of IReminder

[3a] IRnResearchNbkRepository properties: ['Singleton']
[3a] RecordsOC in IRnResearchNbkRepository: False
[3a] Singleton in IRnResearchNbkRepository: True
[3a] RecordsOC in IRnResearchNbk (the Singleton type): True
```

#302's premise is CONFIRMED. IRnResearchNbkRepository's own surface
really is only Singleton (the interface's one property returned by
GetProperties() on the narrowed type) -- no Count was found by this
reflection either, so the issue's stated "Singleton, Count" pairing
should be double-checked by the programmer against the base
IRepository of T generic surface before citing "Count" as confirmed;
this cycle only confirms Singleton and the absence of RecordsOC on the
repository itself. repos.RecordsOC at DataNotebookOperations.py:313,
:393, approximately :2533 must indeed become repos.Singleton.RecordsOC --
confirmed RecordsOC exists on IRnResearchNbk (the Singleton's type), not
on the repository itself.

### 3(b) Service-locator precedent for issue #261

```
[3b] FLExProject.Object source:
    def Object(self, hvoOrGuid):
        """
        Returns the CmObject for the given Hvo or guid (str or System.Guid).
        Refer to .ClassName to determine the LCM class.
        """
        if isinstance(hvoOrGuid, str):
            try:
                hvoOrGuid = System.Guid(hvoOrGuid)
            except System.FormatException:
                raise FP_ParameterError("Invalid parameter, hvoOrGuid")

        if isinstance(hvoOrGuid, (System.Guid, int)):
            return self.project.ServiceLocator.GetObject(hvoOrGuid)
        else:
            raise FP_ParameterError("hvoOrGuid must be an Hvo (int), System.Guid or str")

[3b] Precedent confirmed: flexicon/code/Grammar/EnvironmentOperations.py
__ResolveObject calls self.project.Object(env_or_hvo), which is
FLExProject.Object() -> self.project.ServiceLocator.GetObject(...) --
NOT the raw LcmCache.GetObject(hvo) that DataNotebookOperations.py:187
currently calls directly.
```

File:line precedent: flexicon/code/Grammar/EnvironmentOperations.py:714
(obj = self.project.Object(env_or_hvo) inside __ResolveObject) routes
HVO-to-ICmObject resolution through FLExProject.Object() ->
self.project.ServiceLocator.GetObject(hvoOrGuid)
(flexicon/code/FLExProject.py:3946-3959), NOT the raw LcmCache. This is
the exact call form DataNotebookOperations.py:182/187
(self.project.project.GetObject(hvo) -- self.project.project IS the raw
LcmCache) should be routed through instead for #261.

---

## Test file

tests/operations/test_lcm_member_truth_sweep.py (9 tests, all pass live,
run_mode: live). Makes no production code change; the only write is the
authorized, restored Part 2(d) seeding in sena3_sandbox.

## Result

[PASS] -- ground truth established live for #259 (verdict ii, MsaRA
navigation with mandatory None-check plus concrete-type guard), #283
(RA confirmed, Duplicate currently drops the field entirely rather than
cloning or referencing, correct fix is reference-assignment), and
#302/#261 (both premises confirmed, with a caveat on #302's "Count"
claim needing a second look).
