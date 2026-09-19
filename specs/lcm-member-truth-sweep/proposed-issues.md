# Proposed issues -- Catalogue 2 sibling bugs + T2.4 out-of-scope live findings

**Status: FILED 2026-09-18.** All ten clusters below were opened on
`MattGyverLee/flexicon` as issues **#322-#331** by the main session, under the
user's authorization of 2026-09-18 ("you can file the issues. don't wait for
me"). Each cluster heading now carries its filed issue number. This file
remains the drafting record and the single place where the evidence behind
each issue is gathered.

| Cluster | Issue |
|---|---|
| 1 | [#322](https://github.com/MattGyverLee/flexicon/issues/322) |
| 2 | [#323](https://github.com/MattGyverLee/flexicon/issues/323) |
| 3 | [#324](https://github.com/MattGyverLee/flexicon/issues/324) |
| 4 | [#325](https://github.com/MattGyverLee/flexicon/issues/325) |
| 5 | [#326](https://github.com/MattGyverLee/flexicon/issues/326) |
| 6 | [#327](https://github.com/MattGyverLee/flexicon/issues/327) |
| 7 | [#328](https://github.com/MattGyverLee/flexicon/issues/328) |
| 8 | [#329](https://github.com/MattGyverLee/flexicon/issues/329) |
| 9 | [#330](https://github.com/MattGyverLee/flexicon/issues/330) |
| 10 | [#331](https://github.com/MattGyverLee/flexicon/issues/331) |

- The user authorized filing these on 2026-09-18.
- The **main session** files from this draft using `gh issue create`, after
  the crew's review is complete -- **not** this task (T2.7), which produces
  the draft only.
- No sub-agent that touched this campaign has run `gh` at any point, and
  this task did not either.
- **Operational precondition before filing:** run
  `gh repo set-default MattGyverLee/flexicon` first. This repo carries two
  remotes -- `origin` (`MattGyverLee/flexicon`) and `upstream`
  (`cdfarrow/flexlibs`, the fork parent). With no default set, `gh` prefers
  `upstream`, whose issue numbering tops out near #17, so every issue number
  this project cites (all in the hundreds) resolves to "Could not resolve to
  an issue" -- which reads exactly like "the issue does not exist" but is
  actually "you asked the wrong repo."

**Provenance:** Catalogue 2 (`specs/lcm-member-truth-sweep/catalogue2-siblings.md`,
25 ranked rows, cycle 1), its live upgrades (T2.5/T2.5b,
`evidence/live-T2.5-siblings.md`), and four additional out-of-scope live
findings surfaced incidentally during T2.4
(`reviews/cycle2-programmer-T2.4-T2.5.md`). None of these are among the six
issues chartered for this campaign (#302, #261, #283, #259, #303, #309) and
none are fixed by this campaign (ruling C13, `spec.md` section 3).

**Confidence key:**
- **live-confirmed** -- a live FLEx session (reflection or functional) proved
  the claim under `FLEXLIBS_REQUIRE_LIVE=1`, `run_mode: live`.
- **snapshot-derived** -- cross-referenced against the 257-type / 4,096-member
  LCM snapshot only; strong evidence, not proof. Needs live confirmation
  before a fix lands.

---

## Cluster 1 (FILED #322) -- Notebook/Anthropology `TextsRC` + `RecTypesOA` family

**Proposed title:** `Notebook/Anthropology: LinkToText/UnlinkFromText/AddText/RemoveText silently no-op on a nonexistent TextsRC; RecTypesOA does not exist on ILangProject`

**Rows:** Catalogue 2 #1, #2, #3, #4, plus the `:825` carve-out.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `Notebook/DataNotebookOperations.py:1911,1913` (`LinkToText`) | `record.TextsRC` | `IRnGenericRec` has `TextRA` (atomic ref), no `TextsRC` | silent (write lost -- `hasattr` guard False, method reports success) |
| `Notebook/DataNotebookOperations.py:1952,1954` (`UnlinkFromText`) | `record.TextsRC` | same | silent (unlink no-ops) |
| `Notebook/AnthropologyOperations.py:1403,1407` (`AddText`) | `item.TextsRC` | `ICmAnthroItem` has 0 declared properties beyond base interfaces (`ICmObject`, `ICmObjectOrId`, `ICmPossibility`) | silent (write lost) |
| `Notebook/AnthropologyOperations.py:1461,1465` (`RemoveText`) | `item.TextsRC` | same | silent (write lost) |
| `Notebook/DataNotebookOperations.py:825` | `lp.RecTypesOA` | `ILangProject` has `ResearchNotebookOA`, `StatusOA`, `PartsOfSpeechOA`, etc. -- no `RecTypesOA` under this name (59-property full surface) | silent (`hasattr` guard False; caller sees an empty/no-op type list) |

**Confidence:** live-confirmed (all five rows; T2.5, `evidence/live-T2.5-siblings.md`
table rows 1-4 by full `clr.GetClrType` surface reflection).

**Suggested fix shape:** for the `TextsRC` sites, navigate to the real
association (`IRnGenericRec.TextRA`, singular atomic reference -- confirm the
correct multi-text linking surface, if one exists, before assuming a rename;
absence may mean "there is no collection API here, only a single reference").
For `:825`, locate the correct path to the record-type possibility list
(likely reached via `IRnGenericRec`'s own type reference chain or a
project-level possibility list under a different name) rather than a blind
rename -- same caution as ruling C10 for #259 (navigation, not rename, when
the guarded name is a genuine dead end).

---

## Cluster 2 (FILED #323) -- `NoteOperations`/`annotation.py` replies (`ICmBaseAnnotation` has no `RepliesOS`)

**Proposed title:** `Notebook: NoteOperations.Duplicate/Delete and annotation.py silently drop the reply thread -- ICmBaseAnnotation has no RepliesOS`

**Rows:** Catalogue 2 #6, #7, #8, #9, #10.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `Notebook/NoteOperations.py:383,413` (`Duplicate`, deep) | `source.RepliesOS` / `source_reply.RepliesOS` | `ICmBaseAnnotation` (11-property live surface: `BeginObjectRA`, `EndObjectRA`, `OtherObjectsRC`, `TextAnnotated`, etc.) has no `Replies*` of any kind; `IScrScriptureNote` uses `ResponsesOS` instead | silent (deep copy drops the whole reply thread) |
| `Notebook/NoteOperations.py:345,353` (`Duplicate`, placement) | `parent.RepliesOS` | same | silent (duplicate never attached when parent is a note) |
| `Notebook/NoteOperations.py:263` (`Delete`) | `owner.RepliesOS` | same | silent (reply-owned note never removed from its owner) |
| `Notebook/NoteOperations.py:902,962` | `note.RepliesOS` / `parent_note.RepliesOS` | same | silent |
| `Notebook/annotation.py:498,522` | `self._obj.RepliesOS` | same | silent |

**Confidence:** live-confirmed (T2.5: `ICmBaseAnnotation` full 11-property
live surface has no `Replies*` member; `evidence/live-T2.5-siblings.md` row 5).

**Suggested fix shape:** determine whether replies are modeled at all on
`ICmBaseAnnotation` in this LCM version (possibly only `IScrScriptureNote`
via `ResponsesOS`, a narrower type than the general annotation base every
one of these call sites assumes) before choosing rename vs. remove-the-feature.

---

## Cluster 3 (FILED #324) -- Discourse `ClauseMarkersOS`

**Proposed title:** `Discourse: ConstChartClauseMarkerOperations writes/reads a nonexistent IConstChartRow.ClauseMarkersOS -- markers live in CellsOS`

**Rows:** Catalogue 2 #11, #12, #13.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `Discourse/ConstChartClauseMarkerOperations.py:128` (`Create`) | `row.ClauseMarkersOS` | `IConstChartRow` (snapshot) exposes `CellsOS` only | silent (newly created marker never attached) |
| `Discourse/ConstChartClauseMarkerOperations.py:211,252` | `row.ClauseMarkersOS` | same | silent |
| `Discourse/ConstChartClauseMarkerOperations.py:466` | `parent.ClauseMarkersOS` | same | silent |

**Confidence:** snapshot-derived. Not covered by T2.4/T2.5/T2.5b; needs its
own live `dir()`/reflection pass before a fix is proposed, same as Cluster 6
below.

**Suggested fix shape:** navigate through `CellsOS` to find where clause
markers actually attach, rather than renaming a collection that may not
exist under any suffix.

---

## Cluster 4 (FILED #325) -- sync-payload name / cardinality mismatches

**Proposed title:** `GetSyncableProperties across four Operations classes: name AND cardinality mismatches silently omit data from the sync payload`

**Rows:** Catalogue 2 #14, #15, #16, #17, #18, #19, #20.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `Discourse/ConstChartMovedTextOperations.py:204` | `word_group.MovedTextMarkerOA` | `IConstChartWordGroup` has `BeginSegmentRA/EndSegmentRA/ColumnRA/MergesBefore/MergesAfter` -- no moved-text member | silent (read wrong -- always `None`) |
| `TextsWords/TextOperations.py:390` (`GetSyncableProperties`) | `item.MediaFilesRC` | `IText.MediaFilesOA` -- Owning **Atomic**, not Reference Collection: suffix AND cardinality both wrong | silent (sync payload omits media every time) |
| `Lexicon/EtymologyOperations.py:478` (`GetSyncableProperties`) | `item.LanguageRA` | `ILexEtymology.LanguageRS` -- reference **sequence**, not atomic: suffix + cardinality mismatch | silent (sync payload loses it) |
| `Lexicon/EtymologyOperations.py:387` (`Duplicate`) | `source.LanguageNotesRA` | `ILexEtymology.LanguageNotes` is a bare-named `IMultiString` -- not a reference at all | silent (duplicate drops it) |
| `Lexicon/EtymologyOperations.py:491` | `item.LanguageNotesRA` | same | silent |
| `Lexicon/LexEntryOperations.py:475` | `etymology.LanguageNotesRA` | same, third site | silent |
| `Lexicon/LexReferenceOperations.py:1339` | `item.ReferenceTypeRA` | `ILexReference` has `OwnerType` (bare) and `TargetsRS`; no `ReferenceTypeRA` | silent (sync omits the relation type) |

**Confidence:** snapshot-derived. None of these seven sites were part of
T2.4/T2.5/T2.5b's live scope; each needs its own live reflection pass on
`IConstChartWordGroup`, `IText`, `ILexEtymology`, and `ILexReference` before
filing a fix.

**Suggested fix shape:** for the two clear rename cases (`MediaFilesRC` ->
`MediaFilesOA` with cardinality-aware copy semantics, `LanguageRA` ->
`LanguageRS` with sequence-aware copy semantics), a rename plus a cardinality
fix in the copy/sync logic. For `LanguageNotesRA` (three sites, same wrong
name), drop the `RA` suffix entirely and use `IMultiString` copy semantics
(`CopyAlternatives`, matching the `Title`/`Text` pattern elsewhere in this
same campaign). `ReferenceTypeRA` and `MovedTextMarkerOA` need a navigation
answer, not a rename -- neither name exists under any suffix per the
snapshot.

---

## Cluster 5 (FILED #326) -- phonological wrapper fabricated members

**Proposed title:** `System/Grammar phonological wrappers: SegmentRA, NaturalClassRA, and both LeftPart/RightPartOf{Metathesis,Reduplication}OS name members that do not exist -- always None/[]`

**Rows:** Catalogue 2 #21, #22, #23, #24.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `System/phonological_context.py:330` (`segment`) | `self._concrete.SegmentRA` | `IPhSimpleContextSeg.FeatureStructureRA` (the phoneme link) | silent (`segment` property always `None`) |
| `System/phonological_context.py:359` (`natural_class`) | `self._concrete.NaturalClassRA` | `IPhSimpleContextNC` has `FeatureStructureRA`, `PlusConstrRS`, `MinusConstrRS` | silent (`natural_class` always `None`) |
| `Grammar/phonological_rule.py:295,296,326,330` | `LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS` | `IPhMetathesisRule` models metathesis as `StrucDescOS` plus integer indices (`LeftSwitchIndex/Limit`, `RightSwitchIndex/Limit`, `MiddleIndex/Limit`, `LeftEnvIndex/Limit`, `RightEnvIndex/Limit`) | silent (both properties always `[]`) |
| `Grammar/phonological_rule.py:358,359,390,395` | `LeftPartOfReduplicationOS` / `RightPartOfReduplicationOS` | no member containing "Reduplication" exists anywhere in the 257-type snapshot, and no `PhReduplicationRule` type either -- may be an invented rule family | silent (always `[]`) |

**Confidence:** snapshot-derived for all four (rows 21-24 were not in
T2.5/T2.5b's live scope, which covered only Catalogue 2 rows 1-10 and 25).
Row 23 is marked **high** in the catalogue on type-surface grounds; row 24
is marked **med** because the underlying rule family's existence itself is
unproven, not just the member name.

**Suggested fix shape:** rows 21/22 are navigation fixes
(`.FeatureStructureRA`), same pattern as #259 (C10) elsewhere in this
campaign. Rows 23/24 need a live `dir()` pass on a real `IPhMetathesisRule`
instance (and confirmation that reduplication rules exist at all in this LCM
version) before any fix shape is proposed -- do not rename blind.

---

## Cluster 6 (FILED #327) -- compound-rule contexts (`IMoEndoCompound`/`IMoExoCompound`)

**Proposed title:** `Grammar/compound_rule.py: left_context/right_context/contexts are unconditionally None -- no Context member exists under any suffix on IMoEndoCompound or IMoExoCompound (NOT the #283 bug)`

**Row:** Catalogue 2 #25.

**Status: CLEARED-AND-CONFIRMED, not "wrong name to fix" -- this is a
"document the correct access path" issue, not a rename.** T2.5b's live
`dir()` pass (`evidence/live-T2.5-siblings.md`, Q3) checked all four
surfaces -- `clr.GetClrType(IMoEndoCompound)`, `clr.GetClrType(IMoExoCompound)`,
and live `dir()` on one real instance of each, created via
`MorphRules.CreateCompoundRule()` in `target_sandbox` -- for any member whose
name contains "Context", under any suffix (`OA`, `RA`, `OS`, `RS`, bare).
**Zero matches on all four surfaces.** The real surfaces are:

```
IMoEndoCompound: HeadLast (bool), OverridingMsaOA (IMoStemMsa)
IMoExoCompound:  ToMsaOA (IMoStemMsa)
```

Per ruling **C9** (`spec.md` section 3): `_concrete` is
`IMoEndoCompound`/`IMoExoCompound` (class docstring,
`Grammar/compound_rule.py:80-82`), and this is explicitly **not** the #283
bug (`IPhEnvironment`'s `LeftContextOA`/`RightContextOA` -> real
`LeftContextRA`/`RightContextRA`). A blind `OA -> RA` rename here would be
wrong in **both** directions, because neither suffix exists on either type.

| Site | Member named | What actually exists | Symptom |
|---|---|---|---|
| `Grammar/compound_rule.py:220,244` | `self._concrete.LeftContextOA` / `RightContextOA` | nothing -- no Context-named member under any suffix on either concrete type | silent (`left_context`/`right_context`/`contexts` unconditionally `None`) |

**Confidence:** live-confirmed (T2.5b, both CLR-reflection and live-instance
`dir()`, on real created-and-deleted `MoEndoCompound`/`MoExoCompound`
instances in `target_sandbox`).

**Suggested fix shape:** this is not a member-name bug to correct -- there is
no reference or owned context to navigate to under any name on either
concrete type. The fix (if any is warranted) is documentation: state plainly
in `CompoundRule`'s docstring that `left_context`/`right_context`/`contexts`
are structurally always `None` for compound rules, because LCM does not
model phonological context on `IMoEndoCompound`/`IMoExoCompound` the way it
does on `IPhEnvironment`. If the properties are genuinely dead weight, an
alternative fix shape is removing them and documenting why, rather than
implying with their presence that a context could ever be attached.

---

## Cluster 7 (FILED #328) -- `IRnGenericRec.Title`/`.Text`: crash-on-write, silent-empty-on-read

**Proposed title:** `Notebook/DataNotebookOperations: Create/CreateSubRecord/SetTitle/SetContent/Duplicate crash unconditionally on Title/Text -- IRnGenericRec.Title is a bare ITsString with no get_String/set_String/CopyAlternatives, and IRnGenericRec has no Text member at all`

**Not in Catalogue 2. Surfaced during T2.4 (`reviews/cycle2-programmer-T2.4-T2.5.md`,
finding 1) once T2.2 let `Create()` get past the unrelated #302 crash for the
first time ever, making these four independent defects reachable in
practice.**

`IRnGenericRec.Title` is a **bare `ITsString`** -- assigned directly, with no
`.get_String()`/`.set_String()`/`.CopyAlternatives()` methods (those belong
to `ITsMultiString`/`IMultiString`, not a plain `ITsString`).
`IRnGenericRec` has **no `Text` member at all** under any name.

| Site | Call | Symptom |
|---|---|---|
| `Notebook/DataNotebookOperations.py:323` (`Create`) | `record.Title.set_String(wsHandle, mkstr)` | crash, unguarded -- `AttributeError` propagates on every call |
| `Notebook/DataNotebookOperations.py:328` (`Create`, content) | `record.Text.set_String(wsHandle, mkstr)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:1196` (`CreateSubRecord`) | `subrecord.Title.set_String(wsHandle, mkstr)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:596` (`SetTitle`) | `record.Title.set_String(wsHandle, mkstr)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:698` (`SetContent`) | `record.Text.set_String(wsHandle, mkstr)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:2541,2578` (`Duplicate`/`_DuplicateSubRecordInto`) | `duplicate.Title.CopyAlternatives(source.Title)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:2542,2579` (`Duplicate`/`_DuplicateSubRecordInto`) | `duplicate.Text.CopyAlternatives(source.Text)` | crash, unguarded |
| `Notebook/DataNotebookOperations.py:544` (`GetTitle`) | `ITsString(record.Title.get_String(wsHandle)).Text`, wrapped in `try/except (AttributeError, TypeError)` | **silent** -- returns `""`, masking the fact that Title cannot be read this way at all |
| `Notebook/DataNotebookOperations.py:641` (`GetContent`) | `ITsString(record.Text.get_String(wsHandle)).Text`, same try/except | **silent** -- returns `""` |
| `Notebook/DataNotebookOperations.py:2607` (`GetSyncableProperties`) | `ITsString(record.Title.get_String(wsHandle)).Text` | same failure mode on the sync path |

**Confidence:** live-confirmed (T2.4, `reviews/cycle2-programmer-T2.4-T2.5.md`
finding 1 -- discovered by running the rewritten live test suite against
`target_sandbox` after the #302/#261 fix unblocked `Create()`).

**Suggested fix shape:** for reads, assign `record.Title` / `record.Text`
directly (bare `ITsString`, per the class the actual live type reflects) and
drop the `get_String`/`.Text` chain and the swallowing `except`. For writes,
build the `ITsString` with `TsStringUtils.MakeString(...)` and assign it
directly to `.Title` (`record.Title = mkstr`), matching how the rest of the
file already treats other bare-`ITsString` fields. `Text` has no equivalent
at all on `IRnGenericRec` -- `SetContent`/`GetContent`/`Duplicate`'s `.Text`
copy line need a navigation answer (is content modeled elsewhere on this
type, or not modeled at all?), not a mechanical fix, before any change lands.

---

## Cluster 8 (FILED #329) -- `IRnGenericRec.Status`/`.Type`/`.Confidence`: real names are `StatusRA`/`TypeRA`/`ConfidenceRA`

**Not in Catalogue 2. Surfaced during T2.4, finding 2.**

**Proposed title:** `Notebook/DataNotebookOperations: GetStatus/GetRecordType/GetConfidence always return None and SetStatus/SetRecordType/SetConfidence silently never reach the LCM -- the real members are StatusRA/TypeRA/ConfidenceRA`

The real member names are `StatusRA`, `TypeRA`, `ConfidenceRA` -- not the
bare `Status`/`Type`/`Confidence` every site below guards for.
`GetStatus`/`GetRecordType`/`GetConfidence` silently return `None` always
(the `hasattr` guard is always False). `SetStatus`/`SetRecordType`/
`SetConfidence` write a **throwaway Python-side attribute** that pythonnet
silently accepts on the CLR wrapper object instead of raising -- so the
write appears to succeed but never reaches the LCM at all.

| Site | Member named | Symptom |
|---|---|---|
| `Notebook/DataNotebookOperations.py:742` (`GetRecordType`) | `record.Type` | silent -- always `None` |
| `Notebook/DataNotebookOperations.py:792` (`SetRecordType`) | `record.Type = record_type` | silent -- write discarded, never reaches LCM |
| `Notebook/DataNotebookOperations.py:2145` (`GetStatus`) | `record.Status` | silent -- always `None` |
| `Notebook/DataNotebookOperations.py:2207` (`SetStatus`) | `record.Status = status` | silent -- write discarded |
| `Notebook/DataNotebookOperations.py:2727` (`GetConfidence`) | `record.Confidence` | silent -- always `None` |
| `Notebook/DataNotebookOperations.py:2780` (`SetConfidence`) | `record.Confidence = confidence` | silent -- write discarded |
| `Notebook/DataNotebookOperations.py:2545-2550,2581-2586` (`Duplicate`/`_DuplicateSubRecordInto`) | `source.Type`/`.Status`/`.Confidence` guards | silent -- all three properties silently never copied |
| `Notebook/DataNotebookOperations.py:2615-2623` (`GetSyncableProperties`) | `record.Status`/`.Confidence` guards | silent -- sync payload's `Status`/`Confidence` fields are always `None` |

**Confidence:** live-confirmed (T2.4, `reviews/cycle2-programmer-T2.4-T2.5.md`
finding 2).

**Suggested fix shape:** rename all bare `Type`/`Status`/`Confidence` guards
and reads/writes to `TypeRA`/`StatusRA`/`ConfidenceRA` across every listed
site in the same commit -- this is a genuine rename (the target name and
type are both known and confirmed), not a navigation problem like Clusters 1
and 6. Verify with a live round-trip (write then re-read by HVO) before
closing, per the standing evidence gate.

---

## Cluster 9 (FILED #330) -- `DateOfEvent` is CLR-typed `GenDate`, not `System.DateTime`

**Not in Catalogue 2. Surfaced during T2.4, finding 3.**

**Proposed title:** `Notebook/DataNotebookOperations.SetDateOfEvent raises TypeError on every call -- IRnGenericRec.DateOfEvent is CLR-typed GenDate, not System.DateTime`

`IRnGenericRec.DateOfEvent` is CLR-typed `GenDate`, not `System.DateTime`.
The property exists and reads fine (a `GenDate` object comes back), but
`SetDateOfEvent` raises `TypeError` on every call because it always assigns
a `System.DateTime` (or a string coerced to one via `DateTime.Parse`).

| Site | Call | Symptom |
|---|---|---|
| `Notebook/DataNotebookOperations.py:1064` (`SetDateOfEvent`) | `record.DateOfEvent = date` where `date` is a `System.DateTime` (from `DateTime.Parse` at `:1057`, or passed directly per the docstring's `DateTime.Now` example) | loud -- `TypeError` raised unconditionally, unguarded |
| `Notebook/DataNotebookOperations.py:1003-1004` (`GetDateOfEvent`) | `hasattr(record, "DateOfEvent")` guard, `return record.DateOfEvent` | not broken on its own, but returns a raw `GenDate`, not the `System.DateTime` the docstrings and `SetDateOfEvent`'s own examples imply round-trips |

**Confidence:** live-confirmed (T2.4, `reviews/cycle2-programmer-T2.4-T2.5.md`
finding 3).

**Suggested fix shape:** convert the incoming `System.DateTime`/string to a
`GenDate` before assignment (LCM's `GenDate` constructor or a documented
conversion helper, if one already exists elsewhere in `flexicon/`) rather
than assigning a `System.DateTime` directly. Confirm whether any other
Operations class already solves this exact `GenDate` conversion before
inventing a new helper.

---

## Cluster 10 (FILED #331) -- `Duplicate()`/`GetParentRecord()` sub-record detection is always False live

**Not in Catalogue 2. Surfaced during T2.4, finding 4.**

**Proposed title:** `Notebook/DataNotebookOperations: Duplicate() and GetParentRecord() sub-record detection is always False live -- isinstance() on the raw uncast .Owner, the same bug class Delete() already fixed under #133`

`Duplicate()` and `GetParentRecord()` detect sub-records with
`isinstance(owner, IRnGenericRec)` on the **raw, uncast** `.Owner`. Live,
pythonnet types `.Owner` as the base `ICmObject`, so this `isinstance` check
is **always `False`** regardless of the record's actual position in the
hierarchy -- every `Duplicate()` call, top-level or sub-record, lands in
`ResearchNotebookOA.RecordsOC` instead of the correct parent's
`SubRecordsOS`, and `GetParentRecord()` always returns `None` for a genuine
sub-record. `Delete()` in the **same file** already fixed this exact bug
class under issue #133 via `self._GetTypedOwner(record)`
(`BaseOperations.py:1709`); `Duplicate()`/`GetParentRecord()` were never
updated to match.

| Site | Call | Symptom |
|---|---|---|
| `Notebook/DataNotebookOperations.py:2523` (`Duplicate`) | `isinstance(owner, IRnGenericRec)` on raw `.Owner` | silent -- always `False`; duplicate always placed at top level regardless of source position |
| `Notebook/DataNotebookOperations.py:1255` (`GetParentRecord`) | `isinstance(owner, IRnGenericRec)` on raw `.Owner` | silent -- always returns `None` for a genuine sub-record |
| `Notebook/DataNotebookOperations.py:333,390-392` (`Delete`) | `self._GetTypedOwner(record)` | **correct** -- the reference fix pattern, already in the same file under #133 |

**Additional site noticed while drafting this cluster, not part of T2.4's
four reported findings and not live-tested by this task -- flagged for the
filer to fold in or split out at their discretion:**
`Notebook/DataNotebookOperations.py:243` (`GetAll`) has the identical
`isinstance(owner, IRnGenericRec)` pattern on a raw `.Owner`, used to decide
whether a record is top-level before yielding it. If the bug class is real
for `Duplicate`/`GetParentRecord`, `GetAll` likely silently yields sub-records
as if they were top-level records too. **Confidence: snapshot-derived
(static read only -- not exercised by any live test in this campaign).**

**Confidence:** live-confirmed for the two chartered sites (T2.4,
`reviews/cycle2-programmer-T2.4-T2.5.md` finding 4, and the rewritten
`tests/operations/test_datanotebook_duplicate.py`, which "locks in the
current (buggy) placement... as an honest regression test rather than
asserting the originally-intended position").

**Suggested fix shape:** replace `isinstance(owner, IRnGenericRec)` with
`self._GetTypedOwner(record) is not None` (or equivalent), mirroring
`Delete()`'s already-fixed pattern exactly, at all sites in this cluster --
including the additional `GetAll` site above once someone verifies it live.
The rewritten test's "honest regression test" for the buggy placement will
need to flip the same way `test_260_environment_resolver_gate.py` flips
under ruling **C8** elsewhere in this campaign: keep the test class and its
narrative docstring, invert the assertion, and point at this issue.

---

## Summary table

| Cluster | Rows/sites | Confidence | In Catalogue 2? |
|---|---|---|---|
| 1. Notebook/Anthropology `TextsRC`/`RecTypesOA` | 5 | live-confirmed | yes (#1-4, :825) |
| 2. `NoteOperations` replies | 5 | live-confirmed | yes (#6-10) |
| 3. Discourse `ClauseMarkersOS` | 3 | snapshot-derived | yes (#11-13) |
| 4. sync-payload mismatches | 7 | snapshot-derived | yes (#14-20) |
| 5. phonological wrapper fabricated members | 4 | snapshot-derived | yes (#21-24) |
| 6. compound-rule contexts | 1 | live-confirmed (cleared, not a rename) | yes (#25) |
| 7. `IRnGenericRec.Title`/`.Text` | 10 | live-confirmed | no (T2.4 finding 1) |
| 8. `IRnGenericRec.Status`/`.Type`/`.Confidence` | 8 | live-confirmed | no (T2.4 finding 2) |
| 9. `DateOfEvent` GenDate mismatch | 2 | live-confirmed | no (T2.4 finding 3) |
| 10. `isinstance` owner-detection bug | 3 (+1 unverified) | live-confirmed (2 sites); snapshot-derived (1 extra site) | no (T2.4 finding 4) |

**10 clusters total. 6 fully live-confirmed, 3 snapshot-derived
(Clusters 3, 4, 5), 1 mixed (Cluster 10: two live-confirmed sites plus one
additional snapshot-derived site the drafter noticed but did not verify).**
