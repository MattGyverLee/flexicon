# Binding Rulings -- Issue #325 Syncable Properties

**Task:** T1 (domain rulings)
**Ruling authority:** lex-domain
**Date:** 2026-09-22
**Branch:** fix/325-syncable-properties
**Evidence base:** specs/325-syncable-properties/evidence/live-T0-reflection.md
  + live-T0-*-raw.json (run_mode=live, 6/6 passed)

Implementers follow these rulings without re-litigating. Each ruling cites the
T0 evidence path that grounds it. `needs_human` flags a blocker that requires
human decision before T2 can proceed.

---

## R1 -- ILexEtymology LanguageRS: sync key as ordered GUID list

**Evidence:** live-T0-etymology-raw.json, live-T0-reflection.md lines 80-108

**LCM facts:**
- `LanguageRS` is on the concrete `LexEtymology` impl; NOT on `ILexEtymology`
  interface (`ILexEtymology_static_has_LanguageRS: false`,
  `ILexEtymology_live_has_LanguageRS: true`).
- It is a Reference Sequence (RS suffix) -- ordered, not atomic.
- 0 populated instances in Ejagham Full (1 etymology, 0 with LanguageRS set),
  so element CLR type was not determinable from live data; static knowledge
  places it as ICmPossibility from the Languages list.
- Current code (`EtymologyOperations.py:478`) reads `item.LanguageRA` -- a
  non-existent atomic alias; the hasattr guard makes this a permanent no-op.

**Ruling (BINDING):**

1. Sync key: `language_rs` (list of GUID strings, ordered).
2. Serialization: `[str(lang.Guid) for lang in item.LanguageRS]` on the
   concrete impl. Accessing requires a concrete cast since the field is not on
   the interface -- use `cast_to_concrete()` or `hasattr` guard on the live
   object, not the static interface.
3. Apply strategy: **replace** the entire sequence. Do not merge by position.
   Empty incoming list -> clear the sequence.
4. Unresolved GUID: emit a logger warning (`[WARN] LanguageRS GUID <guid>
   not found; skipped`). Do not raise. Skip that element only.
5. fill_gaps behaviour: if the target already has any LanguageRS entries,
   skip the replace (fill_gaps semantics applied to the whole sequence as a
   unit, consistent with how other RS fields behave).
6. Remove `LanguageRA` from all sync code paths.

---

## R2 -- Drop LanguageNotesRA (IMultiString LanguageNotes already in payload)

**Evidence:** live-T0-etymology-raw.json, live-T0-reflection.md lines 86-108

**LCM facts:**
- `ILexEtymology.Source` is ABSENT from both interface and implementation
  (`ILexEtymology_live_has_Source: false`). There is no Source field.
- `ILexEtymology.LanguageNotes` IS present on the concrete impl as IMultiString
  (`ILexEtymology_live_has_LanguageNotes: true`).
- `LanguageNotesRA` does NOT appear in the live dir (live-T0-etymology-raw.json
  line 35-60). It never existed.
- Current sync code (`EtymologyOperations.py:487-494`) has a hasattr guard on
  `LanguageNotesRA` that evaluates to False at runtime and always emits `None`
  into the props dict. It is dead weight.
- `LanguageNotes` (IMultiString) is already correctly included in the sync
  payload under the stable API key `"Source"` via the mapping at
  `EtymologyOperations.py:436-445`. This path is live and correct.

**Ruling (BINDING):**

1. Remove the `LanguageNotesRA` block from `GetSyncableProperties`
   (lines 483-494) entirely. Do NOT add a replacement key.
2. Remove the `LanguageNotesRA` block from `Duplicate` (lines 387-388).
3. Remove `"LanguageNotesRA"` from `_ra_fields` in `ApplySyncableProperties`
   (line 522).
4. The `"Source"` key (backed by `LanguageNotes` IMultiString) is the correct
   and complete representation. No new key is introduced.
5. The comment at EtymologyOperations.py:334 ("Reference properties copied:
   LanguageNotesRA") must be corrected to remove LanguageNotesRA from the list.

**Note on dispatch plan wording:** "data already under Source" refers to the
stable API key `"Source"` in the syncable-properties dict, NOT to a nonexistent
LCM field named `Source`. T0 confirms `Source` does not exist on the LCM. The
label is a cross-project sync alias only.

---

## R3 -- LexReference: type key, re-parenting policy, TargetsRS in payload

**Evidence:** live-T0-lexref-raw.json, live-T0-reflection.md lines 110-135

**LCM facts:**
- `ILexReference.ReferenceTypeRA` does NOT exist (not in static or live dir).
  Current code (`LexReferenceOperations.py:1339`) reads it under a hasattr
  guard; always evaluates to None at runtime.
- `ILexReference` has: `Name` (MultiUnicodeAccessor, settable), `Comment`
  (MultiStringAccessor, settable), `TargetsRS` (Reference Sequence),
  `OwnerType` (bare property, present in live dir).
- All 58 ILexReference instances in Ejagham Full are owned by `LexRefType`.
  ILexReference is always owned by ILexRefType (this is how FLEx's lexical
  relation system works; ownership is structural, not variable).
- `TargetsRS` element classnames observed: `LexSense` only (in Ejagham Full).
  Entries can also appear as targets per FLEx model (mapping-type-dependent),
  but only LexSense was observed.

**Ruling (BINDING):**

1. **Type key:** Replace `"ReferenceTypeRA"` with `"owner_guid"` in the sync
   payload. Serialize as `str(item.Owner.Guid)` -- the GUID of the owning
   `ILexRefType`. This unambiguously identifies the relation type and does not
   collide with the settable `Name` attribute.
   - Do NOT use a key named `name` as the type discriminator; it shadows the
     settable attribute.
   - `OwnerType` (the integer mapping-type enum) MAY be included as
     `"mapping_type"` for diagnostic purposes but is NOT the primary key.
2. **TargetsRS in payload:** YES. Include `"targets_rs"` as an ordered list of
   GUID strings: `[str(t.Guid) for t in item.TargetsRS]`. This is required to
   reconstruct the relationship on the target side. Elements are resolved by
   GUID; unresolved elements emit a warning and are skipped (same policy as R1).
3. **Diff-only vs re-parenting:** Diff-only within the same owning LexRefType.
   Matching is by `owner_guid` first, then by `targets_rs` content. If an
   incoming sync payload references a different `owner_guid` (different
   LexRefType), that is NOT a property update -- it is a structural change.
   The implementer must delete the old ILexReference from its current owner
   and create a new one under the target LexRefType. Implementers must NOT
   move an ILexReference by reassigning its owner property; FLEx does not
   support re-parenting by assignment.
4. Remove `"ReferenceTypeRA"` from the payload dict and from any
   ApplySyncableProperties handling.

---

## R4 -- IText media key shape (MediaFilesOA -> container -> URIs)

**Evidence:** live-T0-media-raw.json, live-T0-reflection.md lines 45-77

**LCM facts:**
- `IText.MediaFilesOA` is on the concrete `DomainImpl.Text` impl, NOT on the
  `IText` interface (`IText_static_has_MediaFilesOA: false`,
  `IText_live_has_MediaFilesOA: true`).
- `IText.MediaFilesOA` = None in Ejagham Full (no media configured).
- `ICmMediaContainer.MediaURIsOC` is present on the live impl
  (live-T0-reflection.md line 51). The container holds a collection of
  `ICmMediaURI` objects.
- `ICmMediaURI` has `MediaFileRA` (reference to ICmFile) and `MediaURI`
  (string path/URL), both confirmed present.
- Current sync code (`TextOperations.py:394-395`) reads `item.MediaFilesRC`,
  which does not exist on IText under any suffix. The hasattr guard makes this
  a permanent no-op; sync omits media every time.
- The existing `GetMediaFiles()` method (`TextOperations.py:941-943`) uses
  `text_obj.MediaFilesOA.MediaFilesOC` -- note it reads `MediaFilesOC`, but
  T0 reflection found `MediaURIsOC` on the container. This discrepancy is
  flagged below.

**Ruling (BINDING):**

1. Sync key: `"media_uris"` -> list of dicts, each:
   `{"uri": string, "file_guid": string_or_null}`.
   `uri` = `ICmMediaURI.MediaURI`; `file_guid` = `str(ICmMediaURI.MediaFileRA.Guid)`
   if `MediaFileRA` is not None, else null.
2. Access path: the text object must be accessed as the concrete impl
   (use `cast_to_concrete()` or call through the existing `__GetTextObject`
   helper which already accesses the concrete type). Then:
   `text_obj.MediaFilesOA` -> container (None check) -> `MediaURIsOC` ->
   iterate ICmMediaURI elements.
3. Use `MediaURIsOC` (as found by T0), NOT `MediaFilesOC`. The discrepancy
   between `MediaFilesOC` in `GetMediaFiles()` and `MediaURIsOC` from T0
   reflection must be resolved during T2: the implementer must confirm which
   collection name is correct on a live container before finalising the fix.
   If `GetMediaFiles()` is currently broken for the same reason, fix it in the
   same change.
4. The old `"MediaFilesRC"` key must be removed from `GetSyncableProperties`
   and from the docstring (line 369).
5. Apply: if `"media_uris"` key is absent or empty, leave the container as-is
   (don't destroy existing media). If populated, reconcile by URI string
   (add missing, do not delete extras without explicit delete call).

**[needs_human] MediaFilesOC vs MediaURIsOC discrepancy in GetMediaFiles():**
The existing `GetMediaFiles()` at line 943 uses `MediaFilesOC`. T0 only
confirmed `MediaURIsOC`. If `MediaFilesOC` is also a valid alias or if
`MediaFilesOC` is wrong (a second bug), this is a live verification question
that cannot be resolved from T0 alone. T2 implementer must verify on a live
project with actual media files before closing this ruling.

---

## R5 -- IConstChartMovedTextMarker: Create ownership + incomplete Preposed test

**Evidence:** live-T0-discourse-raw.json, live-T0-reflection.md lines 211-252

**LCM facts:**
- `IConstChartMovedTextMarker` has `ColumnRA`, `WordGroupRA`, `Preposed` on the
  concrete impl (all three confirmed present in live dir).
- `set_Preposed` raises `NullReferenceException` on a raw factory instance
  (no WordGroupRA/ColumnRA set). Same NRE pattern as issue #290.
- Full FLEx path -- factory -> `row.CellsOS.Insert` -> `WordGroupRA` set ->
  `ColumnRA` set -> `Preposed` set -- was NOT tested because the Target sandbox
  text had no segments (`word_group_skip_reason` in raw JSON).
- The NRE on a raw factory instance is a necessary condition for the failure,
  not sufficient: setting WordGroupRA and ColumnRA first MAY resolve it (as
  #290 established for the analogous cell type).

**Ruling (BINDING):**

1. **Ownership:** `IConstChartMovedTextMarker` must be created via the factory
   and inserted into `row.CellsOS` (the `IConstChartRow.CellsOS` owning
   sequence) before any property setters are called. Do NOT set properties on
   a raw factory instance that has not been inserted into its owning collection.
2. **Setter order:** Set `WordGroupRA` and `ColumnRA` BEFORE setting `Preposed`.
   This mirrors the #290 resolution for `IConstChartWordGroup` and is the only
   safe ordering given the NRE evidence.
3. **Incomplete Preposed test -- gap handling:** The full FLEx path was not
   exercised. The T2d implementer may adopt one of these two approaches (their
   choice; both are binding-compliant):
   a. **Adopt #290 model + static surface, defer full Preposed proof to T3:**
      Implement the setter-order constraint above, cite #290 evidence in the
      commit as the analogical basis, and add a `# VERIFY in T3` comment.
      T3 verification must exercise the full path with live segments.
   b. **Require T0 follow-on before T2d:** Block T2d on a follow-on T0 test
      that provides real text segments in the Target sandbox. This adds a
      prerequisite task but gives a pre-implementation PASS on Preposed.
   Either path is acceptable; the implementer must declare which in the PR
   description. No third option (claim done without either) is compliant.
4. `IConstChartWordGroup` `MovedTextMarkerOA` (referenced in the original
   issue at `ConstChartMovedTextOperations.py:204`) does NOT exist on
   `IConstChartWordGroup`. That access always returns None. The correct
   navigation is the reverse: from a `ConstChartMovedTextMarker`, read
   `WordGroupRA` to get the referenced word group.

---

## R6 -- GetLanguage/SetLanguage on sequence (warn, don't block; add plural forms)

**Evidence:** live-T0-etymology-raw.json, live-T0-reflection.md lines 80-108

**LCM facts:**
- `LanguageRS` is a Reference Sequence (ordered), not a Reference Atomic.
- Existing `GetLanguage()` (`EtymologyOperations.py:1247`) accesses
  `etymology.LanguageRA` -- a non-existent field; always returns None.
- Existing `SetLanguage()` (`EtymologyOperations.py:1278`) assigns
  `etymology.LanguageRA = language` -- a no-op (field absent).
- Both methods are currently silently broken.
- Access to `LanguageRS` requires a concrete cast (not on the interface).

**Ruling (BINDING):**

1. Add `GetLanguages(etymology)` -> returns ordered list of ICmPossibility
   objects from `LanguageRS`. Access via concrete cast + `hasattr` guard.
   Returns empty list if no languages set.
2. Add `SetLanguages(etymology, languages)` -> replaces the entire `LanguageRS`
   sequence with the provided ordered list. Validates each element. Requires
   write enabled.
3. `GetLanguage(etymology)` is deprecated: emit `logger.warning(
   "[WARN] GetLanguage reads index 0 of LanguageRS (a sequence); use
   GetLanguages() for the full list.")` and return `GetLanguages()[0]` or None.
4. `SetLanguage(etymology, language)` is deprecated: emit a similar warning
   and call `SetLanguages([language])` (replaces the full sequence with a
   single element).
5. Neither deprecated method raises. The warn-don't-block rule applies.
6. Concrete cast note: `LanguageRS` is not on `ILexEtymology`; the impl object
   must be accessed. The existing `__GetEtymologyObject` helper already
   retrieves the live object; the concrete cast is needed in addition.

---

## R7 -- ILexSense DoNotShowMainEntryInRC: drop key entirely

**Evidence:** live-T0-lexsense-raw.json, live-T0-reflection.md lines 152-171

**LCM facts:**
- `DoNotShowMainEntryInRC` is ABSENT from both the `ILexSense` interface and
  the `LexSense` concrete impl:
  `ILexSense_static_has_DoNotShowMainEntryInRC: false`,
  `ILexSense_live_has_DoNotShowMainEntryInRC: false`.
- Current code at `LexSenseOperations.py:673-678` has a hasattr guard that
  always evaluates to False; always sets the key to `frozenset()` in the
  props dict.
- `ApplySyncableProperties` at lines 712 and 756 handles this key in
  `_special_fields` and the publication-RC loop, which is also always a no-op.
- `DoNotPublishInRC` IS present and correct (different field; keep it).

**Ruling (BINDING):**

1. Remove `DoNotShowMainEntryInRC` from `GetSyncableProperties` (lines 672-678).
2. Remove `"DoNotShowMainEntryInRC"` from `_special_fields` tuple (line 712).
3. Remove `"DoNotShowMainEntryInRC"` from the `for field_name in (...)` loop
   in `ApplySyncableProperties` (line 756).
4. Remove any docstring or comment references to this field.
5. Do NOT substitute another field. The FLEx LCM does not expose this concept
   on ILexSense in the installed version (FieldWorks 9+).

---

## R8 -- IText.Name missing from Texts sync: in scope for #325

**Evidence:** live-T0-reflection.md (IText surface), TextOperations.py:350-397

**LCM facts:**
- `IText.Name` is an IMultiString field present on the `IText` interface. It
  is the user-facing title displayed in FieldWorks. It is NOT the same as
  `IText.MediaFilesOA` (which is on the concrete impl only); Name IS on the
  interface.
- `GetSyncableProperties` for IText (`TextOperations.py:350-397`) does NOT
  include `Name`. The docstring note "IText has no Title -- issue #352" refers
  to a `Title` alias that was guarded away, NOT to the `Name` field itself.
  `Name` exists and is functional (`Create`, `Find`, `GetTitle`, `SetTitle`
  all use it successfully).
- This is a sync omission: a cross-project sync of texts will not copy or
  compare the text's name/title. The `Description` field is included but not
  `Name`.

**Ruling (BINDING):**

1. Add `Name` to `TextOperations.GetSyncableProperties`:
   ```python
   if hasattr(item, "Name") and item.Name:
       props["Name"] = self.project.GetMultiStringDict(item.Name)
   ```
2. Add corresponding handling in `ApplySyncableProperties` for IText: apply
   the Name dict as a MultiString (same pattern as Description).
3. Update the docstring to list `Name` under MultiString properties and remove
   the `Title` note (or correct it to say Name is included).
4. This is in scope for #325 because it is the same class of defect: a sync
   payload omission caused by a wrong or missing field access.
5. If a separate issue already tracks this omission (e.g. issue #352 may
   overlap), confirm before closing #325 that both are addressed. Do NOT
   silently skip this on the grounds that #352 exists -- verify the overlap
   explicitly.

---

## Summary table

| Ruling | Decision | Key action |
|--------|----------|------------|
| R1 | LanguageRS -> ordered GUID list, replace strategy, warn on unresolved | Replace `LanguageRA` with `language_rs` key; concrete cast required |
| R2 | Drop LanguageNotesRA (3 sites); "Source" key backed by LanguageNotes already correct | Remove dead RA references; no new key |
| R3 | owner_guid (owning LexRefType GUID) + targets_rs ordered list; re-parent = delete+create | Replace `ReferenceTypeRA`; add `targets_rs` |
| R4 | cast_to_concrete -> MediaFilesOA -> MediaURIsOC -> uri+file_guid dicts | Replace `MediaFilesRC`; verify MediaFilesOC vs MediaURIsOC live |
| R5 | row.CellsOS ownership; WordGroupRA+ColumnRA before Preposed; defer full Preposed to T3 or block on follow-on T0 | Setter order is binding; gap handling is implementer's declared choice |
| R6 | Add GetLanguages/SetLanguages; deprecate singular forms with warn | Warn don't block; concrete cast required |
| R7 | Drop DoNotShowMainEntryInRC entirely (absent from LCM) | Remove from 3 sites |
| R8 | Add IText.Name to sync payload (in scope #325) | Add Name under MultiString properties |

## needs_human blockers

- **R4 media:** MediaFilesOC vs MediaURIsOC discrepancy in existing GetMediaFiles()
  must be resolved on a live project with actual media files before T2 can claim
  the media path is verified. If human cannot supply a project with media, T2
  implementer must document the unverified gap in the evidence file.

No other needs_human blockers. All other rulings are grounded in T0 live
evidence (run_mode=live, 6/6 passed).
