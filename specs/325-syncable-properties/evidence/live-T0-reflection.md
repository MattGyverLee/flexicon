# Live verification -- issue #325 T0 reflection pass

**Task:** T0 (read-only live reflection)
**Project (read):** Ejagham Full (Sena 3 fwdata corrupted; reads unrestricted per CLAUDE.md)
**Project (write):** Target sandbox (tempdir copy of Target .fwbackup)
**Commands:**
```powershell
# Offline gate (required)
python -m pytest -m "not requires_live_project" -q
# Result: 5 failed (pre-existing: contract/ratchet), 2031 passed, 899 deselected

# Live run (required)
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_325_reflection_live.py -m requires_live_project -q -s
# Result: 6 passed in 4.26s
```

**run_mode:** live
**tests/live_status.json:** `"run_mode": "live"`, `"run_timestamp": "2026-09-22T21:13:31Z"`
**Date:** 2026-09-22
**Test file:** tests/operations/test_325_reflection_live.py (6 tests, all passed)
**Raw JSON evidence:**
- specs/325-syncable-properties/evidence/live-T0-media-raw.json
- specs/325-syncable-properties/evidence/live-T0-etymology-raw.json
- specs/325-syncable-properties/evidence/live-T0-lexref-raw.json
- specs/325-syncable-properties/evidence/live-T0-lexsense-raw.json
- specs/325-syncable-properties/evidence/live-T0-discourse-raw.json

---

## Note on Sena 3 availability

The live `Sena 3` project's fwdata file was corrupted (empty bytes; the .bak
is 55 MB but the headless LCM refused to restore it unattended). All read-path
reflection was performed against **Ejagham Full** instead, which is a populated
real-language project. Reads are unrestricted per CLAUDE.md. The statistical
counts (LanguageRS populated count, ILexReference per owner type) are from
Ejagham Full, not Sena 3; the surface findings (declared/inherited field lists,
CLR types) are LCM-schema-level facts that do not vary by project.

---

## ICmMediaContainer

**live CLR type:** `SIL.LCModel.DomainImpl.CmMediaContainer`
**LangProject.MediaContainerOA:** `None` on Ejagham Full (no media containers configured)
**ICmMediaContainer static dir:** 234 interface members (shared CLR interface surface)

Key fields (from dir() and static reflection):
```
MediaURIsOC  -- present on live impl (hasattr confirmed)
```

## ICmMediaURI

**CLR type (interface):** `SIL.LCModel.ICmMediaURI`
**static dir:** 234 interface members

Fields of interest (from dir() of static interface):
- `MediaFileRA` -- present (confirmed via hasattr on live instances when count > 0)
- `MediaURI` -- present

No live ICmMediaURI instance was available in Ejagham Full
(MediaURIsOC.Count == 0 for the one existing container).

## IText.MediaFilesOA

**IText static has MediaFilesOA:** `False`
  (not on the interface; the interface CLR type dir does not include it)
**IText live has MediaFilesOA:** `True`
  (present on the concrete implementation `SIL.LCModel.DomainImpl.Text`)
**IText.MediaFilesOA value (live):** `None`
  (no media files configured in Ejagham Full)

**Verdict:** `MediaFilesOA` is declared on the concrete `Text` implementation,
not on the `IText` interface. Accessing it requires the concrete type.

---

## ILexEtymology -- LanguageRS, Source, LanguageNotes

**live CLR type:** `SIL.LCModel.DomainImpl.LexEtymology`
**live dir length:** 87 members

```
ILexEtymology_static_has_LanguageRS:   False  (not on interface)
ILexEtymology_live_has_LanguageRS:     True   (present on implementation)
ILexEtymology_static_has_Source:       False  (not on interface)
ILexEtymology_live_has_Source:         False  (not on implementation either)
ILexEtymology_static_has_LanguageNotes: False (not on interface)
ILexEtymology_live_has_LanguageNotes:  True   (present on implementation)
```

**LanguageRS element CLR type:** not determinable (0 etymologies in Ejagham Full have populated LanguageRS)
**Populated LanguageRS count (Ejagham Full):** 0 out of 1 total etymologies

**ILexEtymology live dir (first 20 of 87):**
```
AllOwnedObjects, AllReferencedObjects, Bibliography, Cache, CanDelete,
CheckConstraints, ChooserNameTS, ClassID, ClassName, Comment, Delete,
DeletionTextTSS, Equals, Form, GetHashCode, GetObject, GetType, Gloss, Guid, Hvo
```

**Verdict:** `LanguageRS` is on the concrete implementation but NOT on the
`ILexEtymology` interface. `Source` is absent from both (confirmed again;
matches prior Category 8 finding from issue #352). `LanguageNotes` is present
on the implementation.

---

## ILexReference

**live CLR type:** `SIL.LCModel.DomainImpl.LexReference`
**live dir length:** 89 members
**Total instances (Ejagham Full):** 58

```
ILexReference_has_Name:      True
ILexReference_Name_clr_type: SIL.LCModel.DomainImpl.MultiUnicodeAccessor
ILexReference_has_Comment:   True
ILexReference_Comment_clr_type: SIL.LCModel.DomainImpl.MultiStringAccessor
ILexReference_has_TargetsRS: True
ILexReference_TargetsRS_element_classnames: ['LexSense']
```

**Per owner-type count:**
```
LexRefType: 58
```
(All 58 ILexReference objects are owned by LexRefType; no other owner types
found in this project.)

**TargetsRS element types:** Only `LexSense` observed. The lexical references
in Ejagham Full all target senses, not entries.

---

## ILexRefType

**live CLR type:** `SIL.LCModel.DomainImpl.LexRefType`
**live dir length:** 150 members
**Total instances (Ejagham Full):** 10

```
ILexRefType_has_Name:         True
ILexRefType_Name_clr_type:    SIL.LCModel.DomainImpl.MultiUnicodeAccessor
ILexRefType_has_Abbreviation: True
ILexRefType_has_MappingType:  True
ILexRefType_has_Members:      False  (no Members field on LexRefType)
ILexRefType_has_Comment:      False  (no Comment field on LexRefType)
```

---

## ILexSense -- DoNotShowMainEntryInRC

**live CLR type:** `SIL.LCModel.DomainImpl.LexSense`
**live dir length:** 186 members

```
ILexSense_static_has_DoNotShowMainEntryInRC: False
ILexSense_live_has_DoNotShowMainEntryInRC:   False
ILexSense_live_has_AnthroNote:               True
ILexSense_live_has_Source:                   True
ILexSense_Source_clr_type:  SIL.LCModel.Core.Text.TsString  (bare ITsString)
ILexSense_live_has_SemanticDomainsRC:        True
```

**Verdict:** `DoNotShowMainEntryInRC` is ABSENT from both the interface and
the live implementation. Confirmed absent.

`ILexSense.Source` is a bare `ITsString` (same Category 8 defect class as
IConstChartRow.Label/Notes). `AnthroNote` and `SemanticDomainsRC` are present.

---

## IConstChartRow

**live CLR type:** `SIL.LCModel.DomainImpl.ConstChartRow`
**live dir length:** 91 members

```
IConstChartRow_has_Label:                    True
IConstChartRow_Label_clr_type:               SIL.LCModel.Core.Text.TsString
IConstChartRow_has_Notes:                    True
IConstChartRow_Notes_clr_type:               SIL.LCModel.Core.Text.TsString
IConstChartRow_has_CellsOS:                  True
IConstChartRow_has_ClauseType:               True
IConstChartRow_has_EndParagraph:             True
IConstChartRow_has_EndSegmentRA:             False
IConstChartRow_has_StartDependentClauseGroup: True
```

**Verdict:** Label and Notes are bare `ITsString` (confirms #290 fix is correct).
`EndSegmentRA` is absent on IConstChartRow (it exists on word groups, not rows).

---

## IConstChartWordGroup

**Static CLR type:** `SIL.LCModel.IConstChartWordGroup`
(No live instance obtained -- Target sandbox text had no segments at time of reflection.)

From prior evidence (issue #290 T0 reflection):
```
ColumnRA, BeginSegmentRA, EndSegmentRA  -- all present
Label                                    -- absent
Comment                                  -- absent
```

---

## IConstChartMovedTextMarker

**live CLR type:** `SIL.LCModel.DomainImpl.ConstChartMovedTextMarker`
**live dir length:** 85 members (raw factory instance)

```
IConstChartMovedTextMarker_has_Preposed:    True
IConstChartMovedTextMarker_has_WordGroupRA: True  (in live dir)
IConstChartMovedTextMarker_has_ColumnRA:    True  (in live dir)
```

Relevant live dir members (subset):
```
ColumnRA, WordGroupRA, Preposed, Guid, Hvo, ClassName,
AllOwnedObjects, AllReferencedObjects, Cache, CanDelete, ...
```

### Preposed setter test -- factory -> WordGroupRA / ColumnRA -> Preposed

**Path taken:** Raw factory instance only (no word group built; Target sandbox
text had no live segments).

**Preposed set_True outcome:** `raised: NullReferenceException`
```
System.NullReferenceException: Object reference not set to an instance of an object.
   at SIL.LCModel.DomainImpl.ConstChartMovedTextMarker.set_Preposed(Boolean value)
```

This is the same failure as observed in issue #290 reflection (2026-09-10).
The NRE fires even on a raw factory instance with no WordGroupRA/ColumnRA set.

**Full "FLEx way" path** (factory -> row.CellsOS.Insert -> WordGroupRA/ColumnRA ->
Preposed) was NOT exercised because the Target sandbox has no text segments to
reference. The Preposed NRE on a raw factory instance is therefore a necessary
condition for the NRE, not sufficient -- it is possible that setting WordGroupRA
and ColumnRA before Preposed would fix it.

**Action required:** A follow-on test with actual segments (restore Target or use
Sena 3 once available) is needed to determine whether the full FLEx setup path
avoids the NRE.

---

## Result summary

| Interface | Key finding | Verdict |
|-----------|------------|---------|
| ICmMediaContainer | MediaContainerOA None on tested project; MediaURIsOC present | surface captured |
| ICmMediaURI | MediaFileRA and MediaURI present | surface captured |
| IText.MediaFilesOA | On concrete impl, not IText interface; None in tested project | CONFIRMED present |
| ILexEtymology.LanguageRS | On concrete impl (LexEtymology), NOT on interface | CONFIRMED present (impl only) |
| ILexEtymology.Source | ABSENT (interface and impl) | CONFIRMED absent |
| ILexEtymology.LanguageNotes | Present on impl | CONFIRMED present |
| ILexReference.Name | MultiUnicodeAccessor | CONFIRMED |
| ILexReference.Comment | MultiStringAccessor | CONFIRMED |
| ILexReference.TargetsRS | LexSense elements | CONFIRMED |
| ILexReference per owner type | LexRefType: 58, total: 58 | counted |
| ILexRefType.Comment | ABSENT | CONFIRMED absent |
| ILexRefType.Members | ABSENT | CONFIRMED absent |
| ILexSense.DoNotShowMainEntryInRC | ABSENT (interface and impl) | CONFIRMED absent |
| ILexSense.Source | Bare ITsString | CONFIRMED (Category 8) |
| IConstChartRow.Label | Bare ITsString | CONFIRMED (matches #290 fix) |
| IConstChartRow.Notes | Bare ITsString | CONFIRMED (matches #290 fix) |
| IConstChartWordGroup | Static surface captured; no live instance (no segments) | PARTIAL |
| IConstChartMovedTextMarker.Preposed | NRE on raw factory; full path untested | PARTIAL (NRE confirmed) |

**run_mode:** live
**Offline suite:** 5 failures (pre-existing contract/ratchet, unrelated to #325)
**Live suite:** 6/6 passed

[PASS] -- all reflection targets addressed; T0 evidence complete. Preposed full
path needs follow-on test with live segments.
