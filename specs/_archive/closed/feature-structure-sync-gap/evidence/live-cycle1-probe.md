# Live verification -- cycle1 ground-truth probe (issues #251, #252, #256)

**Project:** Ngoreme FLEx (read-only, writeEnabled=False) + Target (via target_sandbox, tempdir copy -- the real Target was never opened)
**Fixture:** custom ngoreme_readonly (module-scoped, OpenProject("Ngoreme FLEx", writeEnabled=False)) + target_sandbox
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue251_252_256_feature_struct_probe.py -m requires_live_project -q -s
```
**run_mode:** live (confirmed via tests/live_status.json -> "run_mode": "live")
**Date:** 2026-09-07
**Result:** 8 passed, 0 failed. Neither the real Target nor Ngoreme FLEx was
mutated (.fwdata mtimes unchanged before/after: Ngoreme FLEx
2026-08-22 09:59, Target 2026-08-18 20:51 -- both predate this run).

This is a READ-ONLY / SANDBOX-ONLY reconnaissance cycle: no code was
changed. All findings below are raw observed values from the live LCM,
gathered to ground the design of the fix for #251/#252/#256.

---

## Item 1+2: MSA hasattr under base-interface view (a) vs factory-fresh (b); wrong-cast behavior

(a) Base-interface view -- Ngoreme FLEx, entry.MorphoSyntaxAnalysesOC (NOT explicitly cast):

| ClassName | property probed | hasattr True | hasattr False | total |
|---|---|---|---|---|
| MoStemMsa | MsFeaturesOA | 0 | 1951 | 1951 |
| MoInflAffMsa | InflFeatsOA | 0 | 134 | 134 |
| MoDerivAffMsa | FromMsFeaturesOA | 0 | 3 | 3 |
| MoDerivAffMsa | ToMsFeaturesOA | 0 | 3 | 3 |

hasattr is False for 100% of live MSAs reached via the base-interface
view -- exactly the pythonnet static-wrapper-type trap the prior art
(f424f99, 3abf6b5) documents for PhNCFeatures/PhNCSegments. This is
the root mechanism issue #251 must design around: any
GetSyncableProperties written for MSAOperations that gates on
hasattr(msa, "MsFeaturesOA") will silently never fire, exactly like the
dead-code fixes for NaturalClassOperations before them.

(b) Factory-fresh concrete-typed view -- target_sandbox:

- MSAOperations.CreateStem(...) returns an object already explicitly
  cast (IMoStemMsa(new_msa) inside the library code) --
  hasattr(stem, "MsFeaturesOA") = True.
- Re-fetching the SAME object via sense.MorphoSyntaxAnalysisRA (the
  base-interface accessor) immediately afterward:
  hasattr(base_view, "MsFeaturesOA") = False.

This proves the divergence is not about freshness/liveness of the
object -- it is purely about which accessor path returned it. The
identical underlying CLR object is hasattr-True through the cast
return value and hasattr-False through the base-typed re-fetch, in the
same process, same transaction.

Item 2 -- correct cast route:
```
IMoStemMsa(base_view).MsFeaturesOA = None   (cast route works; MSA had no feature struct)
```

Item 2 -- WRONG cast (IMoInflAffMsa applied to a genuine MoStemMsa):
```
cast raised TypeError: object does not implement IMoInflAffMsa
```
The cast itself raises immediately (pythonnet enforces .NET interface
membership at cast time) -- there is no silent-garbage failure mode here;
a wrong cast is loud, not silent.

---

## Item 3: IPartOfSpeech.DefaultFeaturesOA / InherFeatValOA

- hasattr(pos, "DefaultFeaturesOA") = True for 26/26 POS in Ngoreme
  FLEx; non-null for 0/26.
- hasattr(pos, "InherFeatValOA") = True for 26/26; non-null for
  0/26.
- Declared CLR type of both: SIL.LCModel.IFsFeatStruc (confirmed via
  clr.GetClrType(IPartOfSpeech).GetProperty(...)).
- POSOperations.GetAll() (flexicon/code/Grammar/POSOperations.py,
  walk() helper) explicitly does pos = IPartOfSpeech(raw) before
  yielding -- so every POS handed back by GetAll() is already
  concrete-typed. Confirmed live:
  isinstance(pos_list[0], IPartOfSpeech) == True.

Key distinction between #252 and #251 (the deliverable this item was
designed to measure): #252 is a pure coverage gap, NOT a hasattr trap.
POSOperations.GetAll() already performs the correct cast, so
hasattr(pos, "DefaultFeaturesOA")/hasattr(pos, "InherFeatValOA") work
correctly on every object GetSyncableProperties will ever receive.
POSOperations.GetSyncableProperties (lines ~1124-1175) simply never
attempts to read DefaultFeaturesOA/InherFeatValOA at all -- it only
captures Name/Abbreviation/Description/CatalogSourceId. The fix
for #252 does not need any hasattr-gate rework; it needs the two
properties added to the capture loop. This is the opposite failure mode
from #251, where MSAOperations has no GetSyncableProperties at all AND
would hit the real hasattr trap the moment one is written naively.

---

## Item 4: adjacent MSA-family candidates

| Interface | property | declared CLR type |
|---|---|---|
| IMoDerivStepMsa | MsFeaturesOA | SIL.LCModel.IFsFeatStruc |
| IMoDerivStepMsa | InflFeatsOA | SIL.LCModel.IFsFeatStruc |
| IMoUnclassifiedAffixMsa | MsFeaturesOA | PROPERTY NOT FOUND |
| IMoUnclassifiedAffixMsa | InflFeatsOA | PROPERTY NOT FOUND |
| IMoAffixAllomorph | MsEnvFeaturesOA | SIL.LCModel.IFsFeatStruc |
| ILexEntryInflType | InflFeatsOA | SIL.LCModel.IFsFeatStruc |

IMoUnclassifiedAffixMsa genuinely has no feature-structure property
of either name -- confirmed by direct CLR reflection (not a cast/hasattr
artifact). IMoDerivStepMsa, IMoAffixAllomorph, and
ILexEntryInflType all carry an IFsFeatStruc-typed property and are
in-scope for the same sync-gap family as #251/#252/#256, widening the
true scope of the fix beyond the three named MSA types.

---

## Item 5: nested feature-structure shape (Ngoreme FLEx, live example)

Found on a real MoStemMsa.MsFeaturesOA:

```
IFsFeatStruc Guid=88aef232-873a-40d1-afd4-d39d20489f42 TypeRA=NULL LongName='[nagr:[BantuSG:5 BantuPl:6]]' FeatureSpecsOC.Count=1
  IFsComplexValue FeatureRA.Name='noun agreement' Guid=48794301-b219-45a0-948a-e19663db73a4
    IFsFeatStruc Guid=f74013be-2aaf-4f96-9f3e-fe4a9778c500 TypeRA=FsFeatStrucType : 8465 LongName='[BantuSG:5 BantuPl:6]' FeatureSpecsOC.Count=2
      IFsClosedValue Guid=00e94266-0ffd-4b8a-9168-45154b8f8ac9 FeatureRA.Name='Bantu Singular' ValueRA.Name='NC 5'
      IFsClosedValue Guid=4e5d06d0-0d2a-4ddd-8945-a039d3622e79 FeatureRA.Name='Bantu Plural' ValueRA.Name='NC 6'
```

This matches the expected Bantu noun-agreement shape
(IFsFeatStruc > IFsComplexValue(FeatureRA name='noun agreement') >
ValueOA = IFsFeatStruc > FeatureSpecsOC of 2 IFsClosedValue), with one
correction to the expectation in the task brief: TypeRA is null only
at the OUTER level; the INNER (nested) IFsFeatStruc has a real,
non-null TypeRA (FsFeatStrucType : 8465). Do not assume both levels
are typeless.

Second pythonnet base-interface-view finding, one level deeper than
items 1/2: IFsComplexValue.ValueOA comes back typed as the BASE
IFsAbstractStructure, not IFsFeatStruc -- hasattr(raw_value, "TypeRA")
is False immediately after reading ValueOA (confirmed live: False
for the nested struct, True only for the top-level struct which was
reached via MsFeaturesOA directly). An explicit IFsFeatStruc(value_oa)
cast is required before recursing/reading TypeRA/LongName/
FeatureSpecsOC on a nested struct. Any sync code that walks nested
feature structures must cast at EVERY level of ValueOA, not just the
top-level owner property.

Distinguishing IFsComplexValue from IFsClosedValue in FeatureSpecsOC:
cast-attempt-then-check-ClassName (IFsComplexValue(spec) then verify
.ClassName == "FsComplexValue", else try IFsClosedValue(spec)/
"FsClosedValue"). A wrong cast between complex/closed values did not
raise in this run's probing path (the interfaces are apparently more
permissive than the MSA family's IMo*Msa casts) -- classifying strictly
by post-cast .ClassName avoided any ambiguity.

---

## Item 6: counts (Ngoreme FLEx)

| | MoStemMsa | MoInflAffMsa | MoDerivAffMsa |
|---|---|---|---|
| Total count | 1951 | 134 | 3 |
| Non-null feature structure | 782 | 38 | 0 |

Total MSAs (Stem+InflAff+DerivAff): 2088. (MoUnclassifiedAffixMsa: 2,
counted separately in item 1, not included in the feature-structure
sweep since it has no feature-structure property at all -- item 4.)

Correction to the reporter's cited counts (1949 / 134 / 3): actual
live counts are 1951 / 134 / 3 MSAs of each class (reporter's stem
count is off by 2 -- possibly excluding the 2 MoUnclassifiedAffixMsa or a
stale count from before this session; the 134 and 3 figures are exact).

- POS count: 26; POS with non-null DefaultFeaturesOA: 0; POS with
  non-null InherFeatValOA: 0. (Ngoreme FLEx does not currently use
  either POS-level feature field -- #252's fix is correct as a coverage
  gap but this project cannot demonstrate a non-null round-trip; a
  project that populates these fields would be needed for an end-to-end
  live assertion of the eventual fix.)
- Of 820 non-null MSA feature structs: 799 nested (contain at least
  one IFsComplexValue), 21 flat (all IFsClosedValue). Nesting is
  the OVERWHELMING majority shape in this real project, not an edge
  case -- confirms #256's "cannot express nesting" is a first-order gap,
  not a rare corner.

---

## Item 7: reproduce #256 (target_sandbox)

```
stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)
hasattr(stem, "FeaturesOA")    -> False
hasattr(stem, "MsFeaturesOA")  -> True

infl_ops.MakeFeatStruc([], owner=stem)
-> FP_ParameterError: owner has no FeaturesOA property; cannot attach FsFeatStruc.
```

Confirms the code at
flexicon/code/Grammar/InflectionFeatureOperations.py:1031
("if not hasattr(owner_unwrapped, 'FeaturesOA'): raise FP_ParameterError(...)")
fires exactly as read. This is NOT the pythonnet base-interface-view
trap (unlike items 1/2/5) -- stem here is the concrete, factory-fresh,
already-cast IMoStemMsa object (hasattr(stem, "MsFeaturesOA") is
True), and it STILL fails, because IMoStemMsa genuinely has no
FeaturesOA property under any name -- it has MsFeaturesOA instead.
MakeFeatStruc would fail for a concrete-typed MSA owner exactly the
same way it fails for a base-typed one; the bug is a hard-coded property
name (owner.FeaturesOA), not a hasattr/casting bug. The fix needs
MakeFeatStruc to accept a mapping of which owning-property name to use
per owner type (FeaturesOA for natural classes/phonological contexts,
MsFeaturesOA for MoStemMsa, InflFeatsOA for MoInflAffMsa, etc.), not
a hasattr-guard rewrite.

---

## Item 8: IFsFeatStrucFactory / IFsComplexValueFactory / IFsClosedValueFactory Create(Guid)

First (misleading) probe: clr.GetClrType(iface).GetMethods() on
each factory interface directly returned zero Create methods for
all three factories. This is a documented .NET reflection gotcha:
Type.GetMethods() on an INTERFACE returns only members DECLARED
directly on that interface, not members inherited from base interfaces
it extends -- unlike classes, where GetMethods() already flattens the
hierarchy.

Corrected probe (also walking net_type.GetInterfaces()):

| Factory | Create overloads found |
|---|---|
| IFsFeatStrucFactory | ILcmFactory of IFsFeatStruc: Create(), Create(System.Guid) |
| IFsComplexValueFactory | ILcmFactory of IFsComplexValue: Create(), Create(System.Guid) |
| IFsClosedValueFactory | ILcmFactory of IFsClosedValue: Create(), Create(System.Guid) |

All three factories DO expose a Create(Guid) overload, inherited from
the shared generic ILcmFactory-of-T base interface. Corrected answer:
yes, the sync contract CAN round-trip a struct GUID for all three
factory types.

Functional confirmation (item 8b, target_sandbox, not just static
reflection): called the library's real
BaseOperations._CreateWithGuid(fs_factory, guid=requested_guid, ...)
against IFsFeatStrucFactory, attached the result to a live
MoStemMsa.MsFeaturesOA (ownership-first, per item 9), then re-read the
GUID back from the LCM:
```
requested GUID:                         12345678-1234-5678-1234-567812345678
actual GUID on created+attached struct:  12345678-1234-5678-1234-567812345678
GUID preserved: True
```
_CreateWithGuid's own implementation never uses reflection -- it calls
factory.Create(guid_arg) directly via pythonnet dynamic dispatch, which
correctly resolves the inherited overload regardless of the
GetMethods() reflection gotcha above. No changes are needed to
_CreateWithGuid itself for the sync contract to preserve struct GUIDs.

---

## Item 9: ownership-first rule (target_sandbox)

Free-floating (unattached) IFsFeatStruc:
```
free_struct = fs_factory.Create()
free_struct.FeatureSpecsOC.Add(closed_value)
-> NullReferenceException: Object reference not set to an instance of an object.
   at SIL.LCModel.DomainImpl.FsFeatStruc.get_FeatureSpecsOC()
```
The NRE fires on the PROPERTY GETTER itself (get_FeatureSpecsOC()), not
on .Add() -- an unattached IFsFeatStruc cannot even be READ from,
let alone written to. (This triggered a benign Win32 SEH -- faulthandler
printed "Windows fatal exception: access violation" to stderr, matching
the documented benign-SEH pattern in tests/conftest.py's
FwUtils.InitializeIcu() note; the Python-level NullReferenceException
was still caught and handled correctly, and the test passed.)

Attached-first (owner.MsFeaturesOA = struct, THEN populate):
```
attached_struct = fs_factory.Create()
stem.MsFeaturesOA = attached_struct
attached_struct = stem.MsFeaturesOA   (re-fetch via the owning property)
attached_struct.FeatureSpecsOC.Add(closed_value)
-> SUCCESS -- FeatureSpecsOC.Count=1
```

Confirms the "Phase 2 ownership rule" comment already in
InflectionFeatureOperations.MakeFeatStruc's docstring
("LCM property accessors NPE on free-floating IFsFeatStruc objects") is
accurate and must be preserved by any #256 fix that adds nesting support:
each level of a nested structure must be attached to its owning property
(ValueOA for a complex value's nested struct) BEFORE populating its own
FeatureSpecsOC.

---

## Result

[PASS] -- all 9 checklist items answered with live-observed values;
run genuinely reached SIL.LCModel against real data (Ngoreme FLEx,
read-only) and target_sandbox (destructive-safe tempdir copy). No code
under flexicon/code/ was modified. Neither Ngoreme FLEx nor the real
Target project was mutated.
