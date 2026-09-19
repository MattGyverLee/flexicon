# Catalogue 2 -- sibling-bug sweep (durable record)

**Provenance:** extracted verbatim from
`specs/lcm-member-truth-sweep/reviews/cycle1-explore.md` lines 346-408,
cycle 1, 2026-09-18.

**Binding ruling:** per `specs/lcm-member-truth-sweep/spec.md` section 3,
ruling **C13** -- Catalogue 2 stays OUT of scope for behaviour change in the
`lcm-member-truth-sweep` campaign. It is **catalogued only, NOT fixed** here.
No production line referenced by any row below is edited by this file or by
the act of writing it.

**Confidence caveat:** every row is **snapshot-derived** (cross-referenced
against the 257-type / 4,096-member LCM snapshot, not a live FLEx session)
unless the row is explicitly marked **live-confirmed**. Snapshot-derived
absence is strong evidence, not proof; live verification is required before
any row is filed or fixed.

---

## Live upgrades

Filled in from `evidence/live-T2.5-siblings.md` (T2.5 and T2.5b), 2026-09-18.
`run_mode: live`, 25/25 tests passed
(`test_datanotebook_duplicate.py` + `test_lcm_member_truth_sweep.py`, of
which 8 are new under T2.5/T2.5b: `test_5a`-`test_5g`, `test_6a`). No
production line for any row below was edited by T2.5/T2.5b.

| Row | Item | Live-confirmation target | Status |
|---|---|---|---|
| 1-2 | `Notebook/DataNotebookOperations.py:1911,1913,1952,1954` | `IRnGenericRec` has no `TextsRC` | **CONFIRMED ABSENT.** Full 34-property live surface has `TextRA` (atomic ref) and no `TextsRC` anywhere. |
| 3-4 | `Notebook/AnthropologyOperations.py:1403,1407,1461,1465` | `ICmAnthroItem` has no `TextsRC` | **CONFIRMED ABSENT.** Live surface is 0 declared properties (base interfaces only: `ICmObject`, `ICmObjectOrId`, `ICmPossibility`). |
| (carve-out) | `Notebook/DataNotebookOperations.py:825` | `ILangProject` has no `RecTypesOA` | **CONFIRMED ABSENT.** Full 59-property live surface has no `RecTypesOA` (has `ResearchNotebookOA`, `StatusOA`, `PartsOfSpeechOA`, etc., but no record-types list under this name). |
| 5 | `Notebook/PersonOperations.py:1067` | `ICmPerson` has no `LanguagesRC` | **CONFIRMED ABSENT.** Live 9-property surface: `PositionsRC`, `PlacesOfResidenceRC`, no `LanguagesRC`. (`ResearchersRC`/`RestrictionsRC` mentioned in the catalogue turn out to live on `IRnGenericRec`, not `ICmPerson` itself -- doesn't change the absence verdict.) |
| 6-10 | `Notebook/NoteOperations.py` (multiple), `Notebook/annotation.py` | `ICmBaseAnnotation` has no `RepliesOS` | **CONFIRMED ABSENT.** Live 11-property surface: `BeginObjectRA`, `EndObjectRA`, `OtherObjectsRC`, `TextAnnotated`, etc. -- no `Replies*` of any kind. |
| C2 pin | `IRnResearchNbkRepository` exposes `Count`/`Singleton` | Interface reflection + functional pin | `Singleton` directly declared via reflection. `Count` does not surface via `clr.GetClrType(...).GetProperties()` on the derived interface (inherited from generic base `IRepository<T>` -- a reflection quirk). Pinned functionally instead (`target_sandbox`, test_5g): `hasattr(repo, "Count")` True, `repo.Count == 1` (real int), `hasattr(repo, "Singleton")` True, `hasattr(repo, "RecordsOC")` False. C2 holds. |
| 25 | `Grammar/compound_rule.py:220,244` | Live `dir()` on a real `MoEndoCompound`/`MoExoCompound` (Q3, task T2.5b) | **CLEARED, not raised.** `IMoEndoCompound` live surface: `HeadLast` (bool), `OverridingMsaOA` (`IMoStemMsa`). `IMoExoCompound` live surface: `ToMsaOA` (`IMoStemMsa`). Zero Context-named members under any suffix (OA/RA/OS/RS/bare) on either type, confirmed via both CLR reflection and live `dir()` on one real created-and-deleted instance of each in `target_sandbox`. `left_context`/`right_context`/`contexts` are unconditionally `None` for both concrete types; there is no reference or owned context to navigate to. Ruling C9 remains binding -- `compound_rule.py` untouched. |

---

## Traps for a future filer

- **C9 (spec.md section 3):** `Grammar/compound_rule.py:220,244` (row 25
  below) is **NOT** the #283 bug. `_concrete` is `IMoEndoCompound` /
  `IMoExoCompound`, and **neither** the `...OA` nor the `...RA` context
  member exists on either type. A blind `OA -> RA` rename -- the fix that
  worked for #283 on `IPhEnvironment` -- would be wrong in **both**
  directions here. This is a separate suspected bug, filed separately, and
  is hands-off in the `lcm-member-truth-sweep` campaign.
- **`IPhSegRuleRHS`'s `...OA` names are legitimately correct on that type.**
  The `LeftContextOA`/`RightContextOA` names that are wrong on
  `IPhEnvironment` (real fix: `LeftContextRA`/`RightContextRA`, see #283 in
  the campaign spec) are genuine, correct members on `IPhSegRuleRHS`, a
  different type. Do not generalize "OA is wrong here" across types that
  merely share a member name.

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
