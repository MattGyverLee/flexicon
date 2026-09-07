# Live verification -- issue #254 investigation probe

**Project:** Sena 3 | **Fixture:** sena3_sandbox (tempdir copy of
`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`, disposed on teardown --
no restore needed, nothing persisted)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue254_morphra_probe.py -m requires_live_project -q -s
```
**run_mode:** live (confirmed via `python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"` -> `live`)
**Date:** 2026-09-06
**Result:** 2 passed

## Claim under test

Issue #254: `WfiMorphBundleOperations.GetMorphType()` / `SetMorphType()`
document `bundle.MorphRA` as an `IMoMorphType`, and `SetMorphType()`
accepts an `IMoMorphType` object and assigns it directly to
`bundle.MorphRA`. This is an INVESTIGATION PROBE, not a fix -- it
establishes ground truth before any design decision.

## Q1 -- actual .NET type / ClassName of `bundle.MorphRA`

Sampled 1932 real `IWfiMorphBundle` objects (via
`analysis.MorphBundlesOS`, iterated across all 6973 wordforms in Sena 3)
with a non-None `MorphRA`:

```
MorphRA ClassName distribution: {'MoStemAllomorph': 697, 'MoAffixAllomorph': 1142}
```

Both are `IMoForm` subtypes. **No `MoMorphType`/`ICmPossibility`
ClassName was ever observed on `bundle.MorphRA`** in the sample.
**[PASS]** -- confirmed: `bundle.MorphRA` is an `IMoForm` subtype
(`MoStemAllomorph` / `MoAffixAllomorph`), never `IMoMorphType`.

## Q2 -- `IMoForm(bundle.MorphRA).MorphTypeRA` and its `Name`

Correct read path is `morph_type.Name.BestAnalysisAlternative.Text`
(the naive `morph_type.Name.get_String(anal_ws)).Text` returned `None`
for every one of the 1932 samples -- a WS-selection pitfall, not a data
gap; the BestAnalysisAlternative path recovers real strings).

`(ClassName, MorphType.Name)` distribution over the sample:

```
('MoStemAllomorph', 'root'):     468
('MoAffixAllomorph', 'prefix'):  819
('MoAffixAllomorph', 'suffix'):  323
('MoStemAllomorph', 'stem'):     222
('MoStemAllomorph', 'enclitic'):   7
```

Concrete examples read back from the LCM:
- **known prefix** -- ClassName=`MoAffixAllomorph`, `MorphTypeRA.Name` = `"prefix"`
- **known suffix** -- ClassName=`MoAffixAllomorph`, `MorphTypeRA.Name` = `"suffix"`
- **known stem**   -- ClassName=`MoStemAllomorph`, `MorphTypeRA.Name` = `"root"`

**[PASS]** -- `IMoForm(bundle.MorphRA).MorphTypeRA.Name` yields the
real morpheme-type string (root/stem/prefix/suffix/enclitic), confirming
this -- not `bundle.MorphRA` itself -- is where the "morph type name" a
user wants actually lives.

## Q3 -- does `ICmPossibility(bundle.MorphRA).Name` raise?

Yes, on the first bundle with a non-None `MorphRA` encountered in the
live sample:

```
TypeError: object does not implement ICmPossibility
```

**[PASS]** -- reported failure mode confirmed verbatim against live
data; `bundle.MorphRA` cannot be cast to `ICmPossibility` at all
(consistent with Q1: it is an `IMoForm`, and `IMoMorphType` -- which
*is* an `ICmPossibility` -- is one level removed, at
`IMoForm.MorphTypeRA`).

## Q4 -- can `bundle.MorphRA` be `None` on real data?

Yes. Of 1932 sampled bundles, 93 had `MorphRA is None`
(~4.8% in this sample; Sena 3 is a populated but not exhaustively
curated corpus, so this is a lower-bound estimate, not a spec).
**[PASS]** -- `None` is a real, non-rare state that any fix must
tolerate (matches the existing `GetMorphType`/`GetSyncableProperties`
`if bundle.MorphRA else None` / `hasattr(...) and item.MorphRA` guards).

## Q5 -- WRITE-PATH PROBE: `SetMorphType(bundle, <IMoMorphType>)`

Ran against `sena3_sandbox` (disposable tempdir copy) only.

Pre-state: real bundle, `bundle.MorphRA.ClassName` = `MoStemAllomorph`
(Hvo captured, GUID stable across the call).

Action: `project.WfiMorphBundles.SetMorphType(bundle, morph_types[0])`
where `morph_types[0]` is a real `IMoMorphType`
(`project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS[0]`,
ClassName=`MoMorphType`, Name=`"particle"`).

Observed:
```
TypeError: SIL.LCModel.DomainImpl.MoMorphType value cannot be converted to SIL.LCModel.IMoForm
```

**This is a CRASH, not silent corruption.** The .NET property setter
for `IWfiMorphBundle.MorphRA` is declared/backed as `IMoForm`, so
pythonnet's marshalling layer rejects the `IMoMorphType` object before
the assignment reaches the LCM object graph. Read-back confirms nothing
changed: the exception fires before `bundle.MorphRA` is mutated, so
`GetForm`/`Duplicate`/`GetSyncableProperties` were not reached in this
branch (the post-corruption diagnostics in the probe test are
unreachable dead code on real data, by design -- they exist to cover
the hypothetical "succeeds silently" branch, which did not occur).

**[PASS as an investigation finding]** -- explicit answer: **CRASH**,
not corruption. Every real call to
`WfiMorphBundleOperations.SetMorphType(bundle, <IMoMorphType object>)`
following the documented usage pattern will raise `TypeError` at the
`bundle.MorphRA = morph_type` line (WfiMorphBundleOperations.py:877)
before any write reaches the LCM.

## Cleanup

`sena3_sandbox` is a tempdir-scoped fixture; the sandbox and its
`.fwdata` were deleted automatically on fixture teardown. The real
Sena 3 project (`C:\ProgramData\SIL\FieldWorks\Projects\Sena 3`) was
never opened or touched by this probe.

## Result

[PASS] -- all 5 questions answered with values read back from a live
LCM cache (`run_mode: live`). Ground truth for issue #254:
`bundle.MorphRA` is always an `IMoForm` (`MoStemAllomorph` /
`MoAffixAllomorph`), sometimes `None`; the morph-type name a caller
wants lives one hop further at `IMoForm(bundle.MorphRA).MorphTypeRA.Name`;
`ICmPossibility(bundle.MorphRA)` fails as reported; and the current
`SetMorphType(bundle, IMoMorphType)` call pattern is a **hard crash**
(`TypeError`), not silent data corruption.
