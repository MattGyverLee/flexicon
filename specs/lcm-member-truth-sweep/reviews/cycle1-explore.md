# cycle1-explore.md -- LCM member truth sweep, cycle 1 exploration

**Campaign:** lcm-member-truth-sweep, cycle 1
**Issues:** #302, #261, #283, #259, #303, #309
**Date:** 2026-09-18

> Provenance note: produced by the `Explore` subagent in strict read-only mode
> (no Write/Edit tool). Persisted to this path verbatim by the main session on
> its behalf. Content is unmodified.

Method note: every "does this member exist" claim below is grounded in
`tests/contract/snapshots/liblcm_baseline.json` (257 reflected LCM types)
and/or already-committed live-reflection evidence in `specs/`. No live LCM
was invoked, nothing was executed against a project, nothing was modified.

The six in-scope issues map to: **#302** (a), **#261** (b), **#283** (c),
**#259** (d), **#303** + **#309** (e).

---

## CATALOGUE 1 -- blast radius

### (a) #302 -- `repos.RecordsOC` on an `IRnResearchNbkRepository` service

Ground truth (snapshot): `IRnResearchNbkRepository` properties = `{Count,
Singleton}`; methods = `{AllInstances, GetObject, TryGetObject, ...}`.
No `RecordsOC`. The real owner is `ILangProject.ResearchNotebookOA`
(`IRnResearchNbk`) -> `.RecordsOC`.

Executable production call sites (3):
- `flexicon/code/Notebook/DataNotebookOperations.py:313` -- `Create()`, `repos.RecordsOC.Add(record)`
- `flexicon/code/Notebook/DataNotebookOperations.py:393` -- `Delete()`, `repos.RecordsOC.Remove(record)` (the else-branch of the `SubRecordsOS` check)
- `flexicon/code/Notebook/DataNotebookOperations.py:2530` -- `Duplicate()`, `repos.RecordsOC.Add(duplicate)` (issue text says ~2533; actual is 2530)

Service-lookup lines that feed them (will need the `.Singleton` hop or an
`lp.ResearchNotebookOA` swap): `:306` (Create), `:376` (Delete), `:2529`
(Duplicate). Note `:232` (`GetAll`) uses `repos.AllInstances()` -- that one
is CORRECT and must not be touched.

Comment/docstring lines naming `RecordsOC` in the same file: `:309`,
`:384`, `:2462`, `:2526`.

Tests to update:
- `tests/operations/test_datanotebook_duplicate.py` -- `:31`, `:104`, `:114`, `:118`, `:142`, `:152`, `:156`, `:157`, `:185`, `:192`, `:193`, `:201`, `:205`
- `tests/operations/test_cycle2_live_299_300_290.py` -- `:116-119` (comment), `:137` (`notebook_obj.RecordsOC.Add(parent)` -- this one is the CORRECT path, keep)
- `tests/operations/test_lcm_member_truth_sweep.py` -- `TestPart3NotebookRepositoryGroundTruth.test_3a_*` (already asserts the truth; keep as ratchet)

Docs to update: `docs/FUNCTION_REFERENCE.md:1076`, `:1079`;
`docs/API_ISSUES_CATEGORIZED.md:696`, `:704`;
`evidence/issue_158_pattern_i_post_datanotebookoperations_2026-05-30.txt:8,10,15,20,26`.

`.pyi`: `flexicon/code/Notebook/DataNotebookOperations.pyi:18` (Create),
`:19` (Delete), `:20` (Duplicate) -- signatures unchanged, **no edit needed**.

**Does any OTHER Operations class make the same repository-vs-Singleton
mistake? NO.** Exhaustive check: 11 `GetService(I*Repository)` sites exist
in `flexicon/code/`. Every one other than the three above consumes the
service through `AllInstances()`, which is a real repository method:
`Lists/ConfidenceOperations.py:165,227`, `Lists/TranslationTypeOperations.py:309`,
`System/AnnotationDefOperations.py:127`, `Grammar/POSOperations.py:917`,
`Lexicon/SemanticDomainOperations.py:811,888`, `Notebook/DataNotebookOperations.py:232`.
A regex sweep for `repo*.<CapitalisedMember>` excluding
`AllInstances|GetObject|TryGetObject|Count` returns **exactly** the three
`RecordsOC` lines and nothing else. Also: `.Singleton` appears **zero**
times anywhere in `flexicon/` -- so there is no existing house precedent
for the Singleton hop; whichever form is chosen will be the first.

**Existing test coverage of the broken path:** `test_datanotebook_duplicate.py`
is a **pure mock re-implementation** -- it never imports
`DataNotebookOperations` (confirmed: the only imports are `warnings` and
`pytest`; `_simulate_duplicate_toplevel` at `:114` re-types the production
logic by hand against a `_MockRepository` that *defines* `RecordsOC`).
It currently PASSES, and it is therefore **asserting the bug**: it
enshrines `repos.RecordsOC.Add(...)` as correct on a fake repository that
has a member the real one does not. This test must be rewritten, not just
re-run. `test_cycle2_live_299_300_290.py` documents the bug in prose and
deliberately routes around it; it is `requires_live_project`-marked, so it
is deselected in ordinary runs.

---

### (b) #261 -- `self.project.project.GetObject(...)` on the raw `LcmCache`

Ground truth (snapshot): `LcmCache` properties = `{ActionHandlerAccessor,
DefaultAnalWs, DefaultPronunciationWs, DefaultUserWs, DefaultVernWs,
Disposing, DomainDataByFlid, IsDisposed, LangProject, LanguageProject,
LanguageWritingSystemFactoryAccessor, MainCacheAccessor,
MetaDataCacheAccessor, ModelVersion, ProjectId, ProjectNameChanged,
ServiceLocator, WritingSystemFactory, kNullHvo}`; methods contain
`GetAtomicPropObject`, `GetText`, etc. -- **no `GetObject`**.

Occurrences of the exact broken pattern `self.project.project.GetObject(` in
the whole repo: **exactly one**.
- `flexicon/code/Notebook/DataNotebookOperations.py:187`, inside
  `__GetRecordObject` (def at `:170`).

House pattern (confirmed by `test_lcm_member_truth_sweep.py:test_3b_*`):
`self.project.Object(hvo)` -> `FLExProject.Object` -> `ServiceLocator.GetObject(...)`.
`ServiceLocator.GetObject` **is** legitimate -- do NOT sweep
`Lexicon/LexSenseOperations.py:1376,1481,1488` (`ServiceLocator.GetObject`)
into this fix; those are the correct shape.

**True blast radius: 38 public methods route through `__GetRecordObject`.**
The issue names only `SetTitle` at `:579` (the call is at `:584`; def at `:545`).
Full list -- `callsite_line (method, def_line)`:

`373 Delete (327)` - `534 GetTitle (499)` - `584 SetTitle (545)` -
`631 GetContent (595)` - `686 SetContent (642)` - `734 GetRecordType (697)` -
`783 SetRecordType (742)` - `909 GetDateCreated (880)` -
`949 GetDateModified (920)` - `994 GetDateOfEvent (960)` -
`1046 SetDateOfEvent (1005)` - `1111 GetSubRecords (1063)` -
`1177 CreateSubRecord (1119)` - `1245 GetParentRecord (1200)` -
`1295 GetResearchers (1259)` - `1349 AddResearcher (1303)` -
`1389 RemoveResearcher (1357)` - `1436 GetParticipants (1399)` -
`1486 AddParticipant (1444)` - `1526 RemoveParticipant (1494)` -
`1574 GetLocations (1536)` - `1630 AddLocation (1582)` -
`1670 RemoveLocation (1638)` - `1718 GetSources (1680)` -
`1773 AddSource (1726)` - `1814 RemoveSource (1781)` -
`1861 GetTexts (1824)` - `1911 LinkToText (1869)` -
`1952 UnlinkFromText (1919)` - `1998 GetMediaFiles (1962)` -
`2051 AddMediaFile (2006)` - `2092 RemoveMediaFile (2059)` -
`2137 GetStatus (2102)` - `2189 SetStatus (2145)` -
`2506 Duplicate (2453)` - `2678 GetGuid (2650)` -
`2717 GetConfidence (2682)` - `2761 SetConfidence (2725)`

Severity amplifier: the `except` clause at `:190-196` catches
`AttributeError`, so the missing-member failure is **masked** and re-raised
as `FP_ParameterError("Invalid notebook record object or HVO: ...")` --
every one of those 38 methods lies about the cause when given an int HVO.

Tests: no test exercises any of the 38 through an HVO.
`test_cycle2_live_299_300_290.py:120-124` documents the defect in a comment
and routes around it. `test_lcm_member_truth_sweep.py:test_3b_*` asserts the
precedent (`EnvironmentOperations.__ResolveObject` uses `self.project.Object`)
and passes. **No existing test asserts the bug; none covers the fix either.**

`.pyi`: `DataNotebookOperations.pyi` has no member-level entries for any of
the 38 (catch-all `__getattr__` at `:24`). **No stub edit required.**

---

### (c) #283 -- `LeftContextOA` / `RightContextOA` in `EnvironmentOperations.py`

Ground truth (snapshot + live, already committed):
`IPhEnvironment` -> `LeftContextRA` / `RightContextRA` (Reference Atomic).
`IPhSegRuleRHS` -> `LeftContextOA` / `RightContextOA` (Owning Atomic).
Those are the **only two** types in the 257-type snapshot carrying either
name.

Executable production lines in `flexicon/code/Grammar/EnvironmentOperations.py` (10):
- `:494`, `:495` -- `GetLeftContextPattern` (hasattr guard + read)
- `:550`, `:551` -- `GetRightContextPattern` (hasattr guard + read)
- `:634`, `:637`, `:641` -- `Duplicate(deep=True)` left-context clone (guard, read, **write**)
- `:646`, `:649`, `:653` -- `Duplicate(deep=True)` right-context clone (guard, read, **write**)

Docstring/comment lines in the same file: `:479`, `:535`, `:564`, `:591`,
`:674-675`, `:746`.

Related-but-CORRECT, do not touch: `flexicon/code/Grammar/PhonologicalRuleOperations.py`
`:639-648`, `:661`, `:672-679`, `:692`, `:874-877`, `:961-970`, `:991-1014`,
`:1041-1046`, `:1087-1098`, `:1145` -- these all operate on `rhs`
(`IPhSegRuleRHS`), where `LeftContextOA`/`RightContextOA` are the real names.
Same for `tests/operations/test_phon_rules.py:272,553,691,694,728,734,742`.

#### TRAP -- `flexicon/code/Grammar/compound_rule.py:220` and `:244`: **SEPARATE, verify before touching -- probably correct as-is; do NOT rename**

`compound_rule.py` reads `self._concrete`, not an `IPhEnvironment`.
`CompoundRule` extends `LCMObjectWrapper` (`..Shared.wrapper_base`) and
uses `cast_to_concrete`; its own class docstring (`:19-22`, `:80-82`) states
`_obj` is `IMoCompoundRule` and `_concrete` is **`IMoEndoCompound` or
`IMoExoCompound`**. The snapshot confirms both concrete interfaces exist
and both list `SIL.LCModel.IMoCompoundRule` among their interfaces.

A blind `OA` -> `RA` rename here would be **wrong in both directions**: the
snapshot shows `IMoEndoCompound` and `IMoExoCompound` carry neither
`LeftContextOA`/`RightContextOA` **nor** `LeftContextRA`/`RightContextRA`
(their surfaces are `LeftMsaOA, RightMsaOA, LinkerOA, OverridingMsaOA,
StratumRA, ToProdRestrictRC, HeadLast` / `ToMsaOA`). So:
- the `#283` fix (`OA`->`RA`) must **not** be applied to `:220`/`:244`;
- these two sites are a *candidate different bug* (silent `None` return
  from `left_context`/`right_context`/`contexts`), which belongs in the
  Catalogue 2 filing, not in this campaign.
- Also touched by the same premise: `compound_rule.py:30` (module docstring)
  and `docs/USAGE_COMPOUND_RULES.md:55-56`.
- Confidence that these are *not* the #283 bug: HIGH. Confidence that they
  are a *separate* bug: MEDIUM (needs live `dir()` on a real
  `MoEndoCompound`; the snapshot's compound-rule coverage may be partial).

**Existing test coverage:** `tests/operations/test_260_environment_resolver_gate.py`
`TestP7DiscoveredWrongPropertyName` (`:264-320`) **does call the production
method** -- `:311` `result = sandbox.Environments.GetLeftContextPattern(env)`
and `:312-317` `assert result is None`. That is a test **asserting the bug**:
it is written as a deliberate "lock the discovery" anchor and will FAIL (as
designed) once #283 is fixed and a populated environment is used. It is
`requires_live_project`-marked, so in a mock run it is deselected, not
passing-and-lying; in a live run it currently passes.
`tests/operations/test_lcm_member_truth_sweep.py:test_2a_*` and `test_2d_*`
are the other anchors -- `test_2d_*` explicitly prints the "field is dropped
entirely" observation for `Duplicate(deep=True)`.
Both files need their assertions inverted as part of the fix.

`.pyi`: `flexicon/code/Grammar/EnvironmentOperations.pyi` has no
`GetLeftContextPattern`/`GetRightContextPattern` entry (catch-all
`__getattr__`). **No stub edit required.**

---

### (d) #259 -- `InflClassRA` on `IWfiMorphBundle`

Ground truth (snapshot): `IWfiMorphBundle` properties =
`{..., Form, InflTypeRA, IsComplete, MorphRA, MsaRA, SenseRA, DefaultSense, ...}`
-- **no `InflClassRA`**. The real homes are `IMoStemMsa.InflectionClassRA`,
`IMoDerivAffMsa.FromInflectionClassRA`/`ToInflectionClassRA`,
`IPartOfSpeech.DefaultInflectionClassRA` / `InflectionClassesOC`,
`IMoAffixAllomorph.InflectionClassesRC`.

Executable production lines (10):
- `flexicon/code/TextsWords/WfiMorphBundleOperations.py:335`, `:336` -- `Duplicate` (guard + **write**; silently drops the field)
- `:385`, `:386` -- `GetSyncableProperties` (guard + read; key silently absent)
- `:1261` -- `GetInflectionClass`, **unguarded** `bundle.InflClassRA` -> raises `AttributeError` on every call (LOUD)
- `:1313` -- `SetInflectionClass`, **unguarded** `bundle.InflClassRA = infl_class` -> raises on every call (LOUD)
- `flexicon/code/TextsWords/WfiAnalysisOperations.py:589`, `:590` -- bundle-copy loop inside `Create`/deep-copy (guard + **write**; silent)
- `flexicon/code/TextsWords/WordformOperations.py:878`, `:879` -- bundle-copy loop (guard + **write**; silent)

Supporting helper: `WfiMorphBundleOperations.py:1471` `__GetInflectionClassObject`
(def) -- resolves the *argument*, survives any fix but its only consumer is
`SetInflectionClass:1310`.

Docstrings/comments to update:
- `WfiMorphBundleOperations.py:289` ("Reference properties copied: ... InflClassRA"),
  `:367`, `:1157` (See Also), `:1200` (See Also), `:1223` (def GetInflectionClass),
  `:1240`, `:1256`, `:1264` (def SetInflectionClass), `:1282`, `:1284`,
  `:1287`, `:1297`
- `WordformOperations.py:785` ("Morph bundle references: SenseRA, MsaRA, MorphRA, InflClassRA")
- `Grammar/POSOperations.py:783-854` `GetInflectionClasses` / `:819-820`
  `pos.InflectionClassesOC` -- **CORRECT**, `IPartOfSpeech.InflectionClassesOC`
  is real; touch only if the fix reroutes through it.
- `docs/FUNCTION_REFERENCE.md:57-58`

`.pyi`: `flexicon/code/TextsWords/WfiMorphBundleOperations.pyi`,
`WfiAnalysisOperations.pyi`, `WordformOperations.pyi` -- none declare
`GetInflectionClass`/`SetInflectionClass`; all catch-all. **No stub edit
required** unless the methods are retired (then remove from
`docs/FUNCTION_REFERENCE.md` and any `_op_aliases` entry).

**Existing test coverage:** `tests/operations/test_lcm_member_truth_sweep.py:69-70`
asserts `"InflClassRA" not in props` on `IWfiMorphBundle` -- a reflection
ratchet that PASSES and correctly asserts the *absence*, i.e. it locks the
bug's premise, not the bug. `tests/operations/test_issue254_live_cycle2.py:341-357`
prints the same answer. **No test exercises `GetInflectionClass` /
`SetInflectionClass` or the three copy loops** -- the two `AttributeError`
call sites are entirely uncovered, and the three silent copy-drops are
entirely uncovered.

---

### (e) #303 / #309 -- `OverlayOperations`

Ground truth (live reflection, already committed in
`specs/277-nonexistent-property-reads/evidence/live-277-overlays.md`):
`ICmOverlay`'s complete own-declared property surface is **`Name`,
`PossItemsRC`, `PossListRA`**. It is **not** an `ICmPossibility`
(`ICmPossibility.IsAssignableFrom(ICmOverlay) == False`). `Name` is a plain
`System.String`, not an `IMultiString`. Overlays are owned project-wide at
`ILangProject.OverlaysOC` (confirmed in snapshot: `ILangProject` has
`OverlaysOC`); `IDsConstChart` has **no** overlay member anywhere in its
hierarchy (snapshot: `IDsConstChart` = `{BasedOnRA, RowsOS, TemplateRA,
HeaderFooterSetsOC, PublicationsOC, Name, Description, ...}`).

**Public methods of `OverlayOperations`** (`flexicon/code/Lists/OverlayOperations.py`),
with their status:

| Method | def | status |
|---|---|---|
| `IsVisible` | :147 | BROKEN -- `IsVisibleRA` (:173,:174) and `Hidden` (:175,:176) both absent -> always returns `True` |
| `SetVisible` | :180 | BROKEN -- silent no-op (:206,:207,:208,:209) |
| `GetDisplayOrder` | :214 | BROKEN -- `SortSpec` absent (:241,:242) -> always `0` |
| `SetDisplayOrder` | :246 | BROKEN -- silent no-op (:276,:278) |
| `GetElements` | :283 | BROKEN -- `InstancesOS`/`Elements` absent (:310,:311,:312,:313) -> always `[]` |
| `AddElement` | :317 | BROKEN -- silent no-op (:345,:346,:348,:349,:350,:352) |
| `RemoveElement` | :355 | BROKEN -- silent no-op (:384,:385,:387,:388,:389,:391) |
| `GetChart` | :396 | BROKEN premise -- `ChartRA`/`Chart` absent (:429,:430,:431,:432); `OwnerOfClass(DsConstChartTags.kClassId)` (:437) always `None` because overlays are `ILangProject`-owned |
| `GetPossItems` | :443 | **FIXED** (#277) -- `PossItemsRC` (:479,:480). Do not regress. |
| `FindByChart` | :486 | BROKEN -- `chart.OverlaysOC`/`chart.Overlays` absent on `IDsConstChart` (:526,:527,:528,:529) -> always `[]` |
| `GetVisibleOverlays` | :534 | BROKEN transitively (calls `FindByChart` then `IsVisible`) |
| `_get_list_object` | :135 | **#309** -- hard-codes `return None` (:140), which breaks every inherited method |

Inherited-from-`PossibilityItemOperations` surface, all non-functional
because `_get_list_object()` is `None` and/or `Name` is a bare string:
`Create` (raises `FP_ParameterError`), `GetAll` (`[]`), `Delete` (no-op),
`Duplicate` (no-op), `Find` (`None`), `Exists` (`False`), `GetName`,
`SetName`, `GetDescription`, `SetDescription` (`ICmOverlay` has no
`Description` at all), `CompareTo`, `GetSyncableProperties`.

Executable broken production lines counted for this issue: **38**
(37 in the 11 methods above + `:140`).

Callers elsewhere:
- `flexicon/code/FLExProject.py:3030-3057` -- `Overlays` property; docstring
  `:3043-3052` already comments out the examples as "currently broken"
- `flexicon/code/_op_aliases.py:69` -- `"Overlay": "Overlays"`
- `flexicon/__init__.py:297-298` and `flexicon/__init__.pyi` -- export
- `examples/lists_overlay_operations_demo.py` -- `:58`, `:61`, `:78`, `:81`,
  `:83`, `:93`, `:97`, `:98-99`, `:107-108`, `:122-124`, `:128-135`, `:143`,
  `:157-164`, `:174`, `:190-197`, `:211`, `:215`, `:220-227` -- the entire
  demo exercises the non-functional inherited CRUD and will need a rewrite
  once #309 lands
- `tests/operations/test_overlay_operations.py` -- `:35` (source-level
  ratchet on `GetPossItems`), `:77-199` (`TestGetPossItemsLive`, 3 tests,
  `requires_live_project`). **Nothing else in `tests/` touches Overlays.**
- Docs: `docs/FUNCTION_REFERENCE.md:905-951` (14 entries, several of which
  document parameters the real class does not take -- e.g. `:909`
  `GetAll(chart_or_hvo)`, `:912` `Create(chart_or_hvo, name, wsHandle)`),
  `docs/MIGRATION_GUIDE.md:168`, `:173`,
  `docs/API_ISSUES_CATEGORIZED.md:92`,
  `docs/sphinx/api/flexicon.code.Lists.rst:31`
- `.pyi`: `flexicon/code/Lists/OverlayOperations.pyi` declares `GetAll`,
  `Find`, `Exists`, `Create`, `Delete`, `Duplicate`, `GetName`, `SetName`,
  `GetGUID` + catch-all. **This is the one stub that WILL need edits** if
  #309 changes signatures or the class stops inheriting
  `PossibilityItemOperations` -- note it currently declares
  `BaseOperations[Any]` as its base, which already disagrees with the source
  (`PossibilityItemOperations`).

**Existing test coverage:** only `GetPossItems` is covered, and that path is
already fixed -- those 3 live tests pass and assert the *correct* behaviour.
The 11 broken methods and the #309 `_get_list_object` have **zero**
coverage. `examples/lists_overlay_operations_demo.py` would fail loudly at
`:93` (`Create` raises) if anyone ran it live.

---

### Catalogue 1 totals

| Issue | executable prod call sites | downstream methods | test lines | doc refs | .pyi edits |
|---|---|---|---|---|---|
| #302 | 3 (+3 service-lookup lines) | -- | 13 + 2 files | 5 | 0 |
| #261 | 1 | 38 | 0 (2 doc-comment refs) | 0 | 0 |
| #283 | 10 | -- | 2 files (both assert the bug) | 3 | 0 |
| #259 | 10 | -- | 2 files (ratchet only) | 3 | 0 |
| #303/#309 | 38 | 12 inherited | 1 file (fixed path only) | 5 | 1 file |
| **TOTAL** | **62** | **50** | | | **1** |

---

## CATALOGUE 2 -- sibling-bug sweep (CATALOGUING ONLY, no fixes, no live verification)

Derivation: 319 `hasattr(obj, "<Name><OA|OS|OC|RA|RC|RS>")` guards exist in
`flexicon/code/`. Cross-referencing the guarded member name against the
4,096 member names in the 257-type LCM snapshot leaves 66 that appear
**nowhere** in the snapshot. Of those, I kept only the ones where the
receiver's type is (i) determinable from the surrounding source and (ii)
itself present in the snapshot -- i.e. absence is evidence, not a coverage
gap. That filter correctly discards false alarms such as
`MorphRuleOperations.py:120 CompoundRulesOS`, `PhonologicalRuleOperations.py:150,266
PhonRulesOS`, `:797,826 FeatConstraintsOS`, `InflectionFeatureOperations.py:1225,1274,1338
FeaturesOC/FeatureConstraintsOC/TypesOC`, and `ConstChartOperations.py:110 ChartsOC`
(all real members on types the snapshot does not carry).

**Top 25 by confidence x severity. 22 of 25 are high-confidence
silent-data-loss.** All #302/#261/#283/#259/#303/#309 sites are excluded
(already in Catalogue 1).

| # | file:line | suspect member | why suspicious | silent/loud | conf |
|---|---|---|---|---|---|
| 1 | `Notebook/DataNotebookOperations.py:1911,1913` (`LinkToText`) | `record.TextsRC` | `IRnGenericRec` (in snapshot) has `TextRA` (atomic ref) and no `TextsRC`; guard False => the link write never happens and the method returns success | **silent (write lost)** | high |
| 2 | `Notebook/DataNotebookOperations.py:1952,1954` (`UnlinkFromText`) | `record.TextsRC` | same; unlink silently no-ops | **silent (write lost)** | high |
| 3 | `Notebook/AnthropologyOperations.py:1403,1407` (`AddText`) | `item.TextsRC` | `ICmAnthroItem` (in snapshot) has no `TextsRC`; `__GetItemObject` docstring confirms the type. Add silently no-ops | **silent (write lost)** | high |
| 4 | `Notebook/AnthropologyOperations.py:1461,1465` (`RemoveText`) | `item.TextsRC` | same | **silent (write lost)** | high |
| 5 | `Notebook/PersonOperations.py:1067` (`Duplicate`) | `source.LanguagesRC` | `ICmPerson` (in snapshot) has `PositionsRC`, `PlacesOfResidenceRC`, `ResearchersRC`, `RestrictionsRC` -- no `LanguagesRC`. Sibling guards on the same lines are real, so this reads as a single wrong name; the duplicate silently loses the languages | **silent (data lost on copy)** | high |
| 6 | `Notebook/NoteOperations.py:383,413` (`Duplicate`, deep) | `source.RepliesOS` / `source_reply.RepliesOS` | notes are `ICmBaseAnnotation` (imports at `:15-19`); snapshot shows no `Replies*` on it -- `IScrScriptureNote` uses `ResponsesOS`. Deep copy silently drops the whole reply thread | **silent (data lost on copy)** | high |
| 7 | `Notebook/NoteOperations.py:345,353` (`Duplicate`, placement) | `parent.RepliesOS` | same; the duplicate is silently never attached when the parent is a note | **silent (write lost)** | high |
| 8 | `Notebook/NoteOperations.py:263` (`Delete`) | `owner.RepliesOS` | same; a reply-owned note is silently not removed from its owner | **silent (write lost)** | high |
| 9 | `Notebook/NoteOperations.py:902,962` | `note.RepliesOS` / `parent_note.RepliesOS` | same | silent | high |
| 10 | `Notebook/annotation.py:498,522` | `self._obj.RepliesOS` | wrapper over the same `ICmBaseAnnotation` | silent | high |
| 11 | `Discourse/ConstChartClauseMarkerOperations.py:128` (`Create`) | `row.ClauseMarkersOS` | `IConstChartRow` (in snapshot) exposes `CellsOS` only; markers live in `CellsOS`. Newly created marker is silently never attached | **silent (write lost)** | high |
| 12 | `Discourse/ConstChartClauseMarkerOperations.py:211,252` | `row.ClauseMarkersOS` | same | silent | high |
| 13 | `Discourse/ConstChartClauseMarkerOperations.py:466` | `parent.ClauseMarkersOS` | same | silent | high |
| 14 | `Discourse/ConstChartMovedTextOperations.py:204` | `word_group.MovedTextMarkerOA` | `IConstChartWordGroup` (in snapshot) has `BeginSegmentRA/EndSegmentRA/ColumnRA/MergesBefore/MergesAfter` -- no moved-text member; returns `None` for every word group | silent (read wrong) | high |
| 15 | `TextsWords/TextOperations.py:390` (`GetSyncableProperties`) | `item.MediaFilesRC` | `IText` (in snapshot) has `MediaFilesOA` (Owning **Atomic**, a `CmMediaContainer`) -- suffix AND cardinality mismatch; the sync payload silently omits media every time | **silent (data lost on sync)** | high |
| 16 | `Lexicon/EtymologyOperations.py:478` (`GetSyncableProperties`) | `item.LanguageRA` | `ILexEtymology` (in snapshot) has `LanguageRS` (reference **sequence**) -- suffix + cardinality mismatch | **silent (data lost on sync)** | high |
| 17 | `Lexicon/EtymologyOperations.py:387` (`Duplicate`) | `source.LanguageNotesRA` | `ILexEtymology.LanguageNotes` is a bare-named multistring -- an `RA` suffix on something that is not a reference at all; duplicate silently drops it | **silent (data lost on copy)** | high |
| 18 | `Lexicon/EtymologyOperations.py:491` | `item.LanguageNotesRA` | same, on the sync path | silent | high |
| 19 | `Lexicon/LexEntryOperations.py:475` | `etymology.LanguageNotesRA` | same wrong name, third site | silent | high |
| 20 | `Lexicon/LexReferenceOperations.py:1339` | `item.ReferenceTypeRA` | `ILexReference` (in snapshot) has `OwnerType` (bare, no suffix) and `TargetsRS`; no `ReferenceTypeRA`. Sync silently omits the relation type | **silent (data lost on sync)** | high |
| 21 | `System/phonological_context.py:330` (`segment`) | `self._concrete.SegmentRA` | `IPhSimpleContextSeg` (in snapshot) exposes `FeatureStructureRA` -- the phoneme link. `SegmentRA` does not exist => `segment` is always `None` | silent (read wrong) | high |
| 22 | `System/phonological_context.py:359` (`natural_class`) | `self._concrete.NaturalClassRA` | `IPhSimpleContextNC` (in snapshot) exposes `FeatureStructureRA`, `PlusConstrRS`, `MinusConstrRS`. `NaturalClassRA` does not exist => always `None` | silent (read wrong) | high |
| 23 | `Grammar/phonological_rule.py:295,296,326,330` | `LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS` | `IPhMetathesisRule` (in snapshot) models metathesis as `StrucDescOS` plus integer indices (`LeftSwitchIndex/Limit`, `RightSwitchIndex/Limit`, `MiddleIndex/Limit`, `LeftEnvIndex/Limit`, `RightEnvIndex/Limit`). Both `*OS` names are fabricated => always `[]` | silent (read wrong) | high |
| 24 | `Grammar/phonological_rule.py:358,359,390,395` | `LeftPartOfReduplicationOS` / `RightPartOfReduplicationOS` | no member containing "Reduplication" exists anywhere in the 257-type snapshot, and no `PhReduplicationRule` type either; likely an invented rule family => always `[]` | silent (read wrong) | med |
| 25 | `Grammar/compound_rule.py:220,244` | `self._concrete.LeftContextOA` / `RightContextOA` | `_concrete` is `IMoEndoCompound`/`IMoExoCompound` (class docstring `:80-82`, `cast_to_concrete`); snapshot shows **neither** `...OA` nor `...RA` context member on either type (surfaces are `LeftMsaOA`, `RightMsaOA`, `LinkerOA`, `OverridingMsaOA`, `StratumRA`, `ToProdRestrictRC`, `HeadLast`/`ToMsaOA`) => `left_context`/`right_context`/`contexts` always `None`. **Explicitly NOT the #283 bug -- do not OA->RA it.** Needs live `dir()` before filing | silent (read wrong) | med |

Runner-up candidates deliberately left out of the top 25 (kept here so they
are not lost, ranked below the cut):
- `Notebook/NoteOperations.py:121` -- `ServiceLocator.GetService(ICmBaseAnnotation).Repository`: a service-locator misuse (asking for a *model interface* from `GetService`, then `.Repository` on it) rather than `GetService(ICmBaseAnnotationRepository)`. **Loud**, med confidence.
- `Grammar/InflectionFeatureOperations.py:179` -- `morph_data.ProdRestrictOA`: `IMoMorphData` is not in the snapshot, so absence is unproven. Silent, low-med.
- `Lists/OverlayOperations.py` `SortSpec`/`Hidden`/`Elements`/`Chart` bare-name fallbacks -- folded into #303, not double-counted.

Explicitly cleared during the sweep (do **not** file): `LcmCache`
service-locator-shaped reads `self.project.project.ServiceLocator.*`,
`.DefaultAnalWs`, `.DefaultVernWs`, `.LangProject`, `.ActionHandlerAccessor`
(all real `LcmCache` members per snapshot); and
`Lexicon/LexSenseOperations.py:1376,1481,1488`
`ServiceLocator.GetObject(...)` -- this is the documented house pattern
behind `FLExProject.Object()`, confirmed by
`tests/operations/test_lcm_member_truth_sweep.py:test_3b_*`.

---

## Cross-cutting observations for the fix campaign

1. **Two existing tests currently assert the bug and will go red on a
   correct fix, by design:** `test_260_environment_resolver_gate.py:311-317`
   (#283) and `tests/operations/test_datanotebook_duplicate.py` in its
   entirety (#302 -- and it is worse than a bug-asserting test: it never
   imports the production module, so it would keep passing no matter what
   `Duplicate()` does).
2. **`.pyi` risk is near zero.** All five affected stubs
   (`DataNotebookOperations.pyi`, `EnvironmentOperations.pyi`,
   `WfiMorphBundleOperations.pyi`, `WfiAnalysisOperations.pyi`,
   `WordformOperations.pyi`) are generic 10-line files ending in
   `def __getattr__(self, name: str) -> Any: ...`. The only stub that needs
   real work is `Lists/OverlayOperations.pyi`, and it is already wrong
   independently of this campaign (declares base `BaseOperations[Any]`
   where the source says `PossibilityItemOperations`).
3. **`.Singleton` has zero occurrences in `flexicon/`.** Whichever form #302
   adopts (`repos.Singleton.RecordsOC` vs `self.project.lp.ResearchNotebookOA.RecordsOC`)
   sets the house precedent; the latter matches the shape already used by
   `test_cycle2_live_299_300_290.py:136-137` and by
   `EnvironmentOperations.Duplicate` (`self.project.lp.PhonologicalDataOA`).
4. **Catalogue-2 candidate #1-#4 share `DataNotebookOperations`/`AnthropologyOperations`
   with issues #302 and #261.** If the campaign opens those two files
   anyway, the `TextsRC`/`RecTypesOA` family (Catalogue 2 rows 1-4 plus
   `DataNotebookOperations.py:825`, where `ILangProject` has no `RecTypesOA`
   -- it lives on `IRnResearchNbk`, making `GetAllRecordTypes()` return `[]`
   for every project) is the highest-yield adjacent cluster. It is still
   **out of scope** and belongs in the separate filing.
