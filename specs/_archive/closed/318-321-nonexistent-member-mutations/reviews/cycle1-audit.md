# Cycle 1 audit -- nonexistent-member mutations/guards beyond #317-#320

Source of truth: `C:/Github/FlexToolsMCP/src/flextoolsmcp/index/liblcm/liblcm_api_v11.0.0.json`
(grepped by property name, never read whole; class-scoped by line-range around each hit).

## Coverage (what was actually checked)

- `\.OwningList\b` across flexicon/code -- 3 hits, all KNOWN (#318).
- `hasattr\(` across flexicon/code -- **724 hits across 66 files**. Every literal
  `hasattr(x, "PascalCaseName")` call (`-o` dump, 687 lines) was read; suspicious
  ones (bare names shadowing a `*RA`/`*RC`/`*OS`-suffixed sibling, or names absent from
  the reflection index entirely) were verified against the JSON. Clean, boring
  ones (`ClassName`, `Hvo`, `DateCreated`, `Description`, `Owner`, `Guid`,
  `SubPossibilitiesOS`, `FeaturesOA`, `StratumRA`, etc.) were spot-checked and are
  real CmObject/Possibility members -- not re-litigated individually here.
- `getattr\([^,]+,\s*"[A-Za-z_]+",\s*(None|\[\]|0|False|\{\})\)` -- ~120 hits,
  spot-checked only (mostly `ClassName`/`Hvo`/`IsValidObject`, all real).
- `except AttributeError` -- 17 hits across 8 files. **Not individually traced**
  this cycle -- flagging as a coverage gap for a follow-up sweep.
- `lcm_casting.py:791-823` duck-typing (`Count`/`Add`) -- KNOWN (#321), not
  re-litigated.

## NEW findings

### 1. `Notebook/DataNotebookOperations.py` -- bare `Type`/`Status`/`Confidence` (real: `TypeRA`/`StatusRA`/`ConfidenceRA`)

Sites: `GetRecordType`/`SetRecordType` (736, 786 -- **no hasattr guard at all** on the
set), `GetStatus`/`SetStatus` (2139, 2201), `GetConfidence` (2719, and its `SetConfidence`
just below), `Duplicate` (2537-2546), `_DuplicateSubRecordInto` (2573-2581),
`GetSyncableProperties`/`CompareTo` (2602-2620).

IRnGenericRec's actual RA properties are `TypeRA`, `StatusRA`, `ConfidenceRA`
(confirmed in the index at IRnGenericRec's property block) -- there is no bare
`Type`/`Status`/`Confidence`. Every `Get*` guarded by `hasattr(record, "Type")`
etc. silently returns `None`. `SetRecordType` has **no guard** and does
`record.Type = record_type` directly -- on a Python-side proxy this creates a
throwaway instance attribute rather than raising, so the call reports success
and the record's type is never actually changed. Same shape for `Duplicate`'s
field-copy branches: copies silently skip Type/Status/Confidence on every
duplicated record.

Severity: **P0** for `SetRecordType`/`SetStatus`/`SetConfidence` (silently
discards a user-requested write, no exception); **P1** for the `Get*`/`Duplicate`/
sync paths (unconditional no-op / permanently-empty field).

### 2. `Notebook/DataNotebookOperations.py` -- `TextsRC` (no such property on `IRnGenericRec`; real relationship is singular `TextRA`)

`GetTexts`/`LinkToText`/`UnlinkFromText` (1863, 1913, 1954). `TextsRC` does not
exist anywhere in the LCM 11 index -- confirmed by a whole-index grep for
`"name": "TextsRC"` returning zero matches. The real relationship is one
`TextRA` per record, not a collection. All three methods are unconditional
no-ops; the docstrings' "multiple texts can be linked" claim is fictional.

Severity: **P1**.

### 3. `Notebook/DataNotebookOperations.py` -- `MediaFilesOS` on `IRnGenericRec` (property does not exist on this class)

`GetMediaFiles`/`AddMediaFile`/`RemoveMediaFile` (2000, 2053, 2094). Confirmed
absent from IRnGenericRec's full property list. Unconditional no-op.

Severity: **P1**.

### 4. `Notebook/AnthropologyOperations.py` -- `TextsRC` on `ICmAnthroItem` (property doesn't exist anywhere in LCM 11)

`GetTexts`/`AddText`/`RemoveText`/`GetTextCount` (1343, 1403, 1407, 1461, 1465,
1508). Whole-index grep for `TextsRC` is zero matches. `AddText`/`RemoveText`'s
own "already linked"/"not linked" validation is gated behind the same false
`hasattr`, so those errors also never fire -- calling `AddText` reports success
and links nothing (exact #317 symptom: reports success, does nothing).

Severity: **P1**.

### 5. `Notebook/AnthropologyOperations.py` -- `ResearchersRC` on `ICmAnthroItem` (this property exists only on `IRnGenericRec`, a different class)

`GetResearchers`/`AddResearcher`/`RemoveResearcher` (1609, 1667, 1671, 1725,
1729). Same shape as #4 -- a name real on one class, copy-pasted onto an
unrelated class. Unconditional no-op.

Severity: **P1**.

### 6. `Lexicon/SemanticDomainOperations.py` -- bare `Questions` (doesn't exist; real data lives in `QuestionsOS`, an owned sequence of `CmDomainQ` objects, each with its own `.Question` multistring)

`GetSyncableProperties` (1258-1263). Whole-index grep for `"name": "Questions"`
is zero matches (only `QuestionsOS` exists, confirmed elsewhere in the same
file at line 563 used correctly). The sync/compare tool silently reports the
domain's elicitation questions as always empty.

Severity: **P1** (silently-wrong field in an advertised sync/diff feature).

## Spot-checked and CLEAN (not new bugs)

- `Lists/OverlayOperations.py:429-528` -- `ChartRA`/`Chart`, `OverlaysOC`/`Overlays`,
  `IsVisibleRA`/`Hidden`, `SortSpec`. Verified `Hidden` and `SortSpec` are real
  CmOverlay properties and the `IsVisibleRA`-fails/`Hidden`-succeeds and
  `ChartRA`-fails/ownership-walk-succeeds fallbacks are correctly reachable
  (commented with issue #149/#277 provenance). Outside the already-known
  #320 range (283-391) but not a new bug.

## KNOWN (already filed, not re-litigated)

#318 (LexEntryOperations.py:3138,3209 + LexSenseOperations.py:3885,
`dupe.OwningList.Remove`); #319 (DataNotebookOperations.py Researchers/
Participants ~1297-1528 -- note findings #1/#2/#3 above are *additional*,
non-overlapping bugs in the same file); #320 (OverlayOperations.py 283-391,
InstancesOS/Elements); #321 (WritingSystemOperations.py:495-501,
lcm_casting.py:791-823).

## Not covered this cycle (flag for follow-up)

- The 17 `except AttributeError` sites (FLExProject.py, LexEntryOperations.py,
  LexSenseOperations.py, CustomFieldOperations.py, AnthropologyOperations.py,
  DataNotebookOperations.py, wrapper_base.py x2) were not individually traced.
- ~120 `getattr(..., default)` sites were spot-checked, not exhaustively verified.

---
**Reviewed By:** QC Agent (pattern audit)
