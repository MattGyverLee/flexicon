# TASKS -- lcm-member-truth-sweep

Derived from `spec.md` sections 3-5 (rulings C1-C14, questions Q1-Q4).
Issues: #302, #261, #283, #259, #303, #309.
Baseline commit: `598f41e` (v4.8.0).

**Every task inherits the standing gates in `spec.md` section 6.** In
particular: live verification is REQUIRED for anything touching an
Operations class; `tests/live_status.json` must read `"run_mode": "live"`;
never run bare `pytest`.

**Status legend:** `[ ]` open - `[x]` done - `[B]` blocked on a question.
Mark a task done only when its evidence file exists.

---

## Checkpoint 1 -- ground truth + spec (DONE, spurt 1)

- [x] **T1.1** Live reflection sweep of all six issues' member surfaces.
      -> `evidence/live-cycle1-reflection.md`, `reviews/cycle1-verification.md`
- [x] **T1.2** Domain ruling on the `OverlayOperations` rewrite.
      -> `reviews/cycle1-domain.md`
- [x] **T1.3** Blast-radius catalogue + sibling-bug catalogue.
      -> `reviews/cycle1-explore.md`
- [x] **T1.4** Reflection ratchet test file (9 tests, live-passing).
      -> `tests/operations/test_lcm_member_truth_sweep.py`
- [x] **T1.5** Campaign spec and task list. -> `spec.md`, this file

---

## Checkpoint 2 -- #302 + #261, `DataNotebookOperations.py` (DONE, spurt 2)

Both issues live in one file and total four executable lines. Do them in
one spurt; they share a live evidence run.

- [ ] **T2.1 (gates C1, answers Q1)** Live probe: on **both** Target and
      Sena 3, assert `project.lp.ResearchNotebookOA is not None` and that
      its `Hvo` equals
      `ServiceLocator.GetService(IRnResearchNbkRepository).Singleton.Hvo`.
      Read-only; `target_sandbox` + `sena3_sandbox`.
      -> `evidence/live-T2.1-notebook-owner.md`.
      **If the probe fails, STOP and flip C1 to `repos.Singleton.RecordsOC`
      before writing any fix** -- do not "fix forward" past a failed gate.

- [ ] **T2.2 (#302, C1, C3)** Rewrite `Notebook/DataNotebookOperations.py`
      `:313` (`Create`), `:393` (`Delete` else-branch), `:2530`
      (`Duplicate`) to `self.project.lp.ResearchNotebookOA.RecordsOC`, and
      delete the now-dead `GetService(IRnResearchNbkRepository)` lookups at
      `:306`, `:376`, `:2529`. **Do not touch `:232`** (`AllInstances()` is
      correct). Update the comments/docstrings at `:309`, `:384`, `:2462`,
      `:2526`.

- [ ] **T2.3 (#261, C6)** Rewrite `:187` in `__GetRecordObject` to
      `self.project.Object(hvo)` (precedent:
      `Grammar/EnvironmentOperations.py:714`). Then narrow the `except` at
      `:190-196` so a real `AttributeError` is no longer laundered into
      `FP_ParameterError`; chain the cause with `raise ... from e` at
      minimum. **Do not touch** `Lexicon/LexSenseOperations.py:1376,1481,1488`
      (`ServiceLocator.GetObject` is the correct shape there).

- [ ] **T2.4 (C4)** Delete and rewrite
      `tests/operations/test_datanotebook_duplicate.py`. The replacement
      MUST `import` `DataNotebookOperations` and MUST include at least one
      `requires_live_project` case that creates a record, re-reads it by
      HVO from `RecordsOC`, and deletes it -- all in `target_sandbox`. A
      mock-only replacement does not discharge this ruling. Also add a
      live case that calls **at least three** of the 38 `__GetRecordObject`
      methods **by int HVO** (suggest `GetTitle`, `SetTitle`, `GetStatus`),
      which is the path T2.3 fixes and which currently has zero coverage.

- [ ] **T2.5 (C13 carve-out)** While the live session is open, extend
      `tests/operations/test_lcm_member_truth_sweep.py` with
      **absence-only** reflection assertions (no production edits) for:
      `IRnGenericRec` has no `TextsRC`; `ICmAnthroItem` has no `TextsRC`;
      `ILangProject` has no `RecTypesOA`; `ICmPerson` has no `LanguagesRC`;
      `ICmBaseAnnotation` has no `RepliesOS`. Also pin C2:
      `IRnResearchNbkRepository` exposes `Count` and `Singleton`.
  - [ ] **T2.5b (Q3)** Same session: live `dir()` on a real
        `MoEndoCompound`/`MoExoCompound`, recording whether any
        left/right-context member exists under any suffix. Record the answer
        in the evidence file even if it clears row 25.

- [ ] **T2.6 (C13)** Copy Catalogue 2 verbatim from
      `reviews/cycle1-explore.md` into
      `specs/lcm-member-truth-sweep/catalogue2-siblings.md`, with a header
      naming its provenance and the live upgrades from T2.5/T2.5b.

- [ ] **T2.7 (C13)** Draft `specs/lcm-member-truth-sweep/proposed-issues.md`
      -- one titled, ready-to-file entry per Catalogue 2 cluster (suggest
      grouping: Notebook `TextsRC`/`RecTypesOA`; `NoteOperations` replies;
      Discourse `ClauseMarkersOS`; sync-payload name/cardinality mismatches;
      phonological wrapper fabricated members; compound-rule contexts).
      **Do not file anything.** This is a `needs_human` gate -- the user
      approves which issues get opened. Confirm
      `gh repo set-default MattGyverLee/flexicon` before any future `gh`
      issue call.

- [x] **T2.8** Live verification of T2.2-T2.4 against `target_sandbox`,
      with pre/post state **re-read by HVO**. -> `evidence/live-T2-notebook.md`.
      Plus the offline regression run (`-m "not requires_live_project"`) with
      the pass count recorded and compared to the `598f41e` baseline.

- [x] **T2.9** Commit and push. Suggested subject:
      `fix(notebook): route record resolution through project.Object and own RecordsOC (#302, #261)`.
      Note the close-keyword hazard in `spec.md` gate 7.

**Checkpoint:** #302 and #261 fixed, live-verified, the non-test replaced by
a real one, Catalogue 2 made durable and drafted for filing.

---

## Checkpoint 3 -- #283, `Grammar/EnvironmentOperations.py` (DONE, spurt 3)

- [x] **T3.1 (C7)** Rename `LeftContextOA`/`RightContextOA` ->
      `LeftContextRA`/`RightContextRA` at `:494,495,550,551` (the two
      `Get*ContextPattern` readers).
- [x] **T3.2 (C7)** In `Duplicate`, replace the whole `if deep:` context
      block (`:633-653`) with unconditional reference assignment
      (`duplicate.LeftContextRA = source.LeftContextRA`, likewise Right),
      deleting the `clone_properties` / `NewObject(ClassID)` machinery and
      **both bare `except Exception: pass` swallows**.
- [x] **T3.3 (C7)** Keep `deep` in the signature (pinned at
      `EnvironmentOperations.pyi:18`); document it as inert for this method
      in the docstring `Args`/`Notes` (currently `:564-565`, `:591`) and add
      a CHANGELOG entry.
- [x] **T3.4 (Q4)** Grep `flexicon/`, `examples/`, `tests/` for
      `deep=False` against this method; record the answer in the evidence
      file. If a real caller exists, state its expectation explicitly before
      T3.2 lands.
- [x] **T3.5 (C8)** Invert `test_260_environment_resolver_gate.py:311-317`
      in the **same commit**; keep the class and its narrative docstring,
      add a pointer to this spec. Do the same for the `test_2a_*`/`test_2d_*`
      anchors in `test_lcm_member_truth_sweep.py`.
- [x] **T3.6 (C9)** Explicitly confirm in the evidence file that
      `Grammar/compound_rule.py:220,244` was NOT touched, and that the
      `IPhSegRuleRHS` sites in `PhonologicalRuleOperations.py` (`:639-1145`)
      and `tests/operations/test_phon_rules.py` were NOT touched -- those
      `...OA` names are correct on that type.
- [x] **T3.7** Live verification: seed contexts in `target_sandbox`,
      `Duplicate`, re-read both source and duplicate **by HVO**, assert the
      duplicate's contexts are non-null and are the **same objects** (HVO
      equality) as the source's. -> `evidence/live-T3-environment.md`.
- [x] **T3.8** Commit and push.

**Checkpoint:** environment contexts survive `Duplicate`, proven by HVO
identity, with the two bug-asserting anchors flipped in the same commit.
**MET** (spurt 3) -- source `152223`/`152224`, duplicate re-read by its own
HVO `152223`/`152224`, identical and non-null, `run_mode: live`.

Two recorded deviations, both authorized by the lead at the cycle-3 gate:

- **Fixture:** T3.5(a)'s new seeded test and all of T3.7 ran on
  `sena3_sandbox`, not T3.7's nominal `target_sandbox`. Building a legal
  `IPhSimpleContextSeg` needs an existing `IPhPhoneme` for
  `FeatureStructureRA`, and Target is "mostly blank scratch" with no
  guaranteed phoneme inventory. Sandbox-only either way, so the standing
  gate-1 requirement (tempdir copy, nothing touches a real project) is
  fully met.
- **Deferred coverage:** the delete-survival path is not exercised --
  tracked as **T8.6**, see checkpoint 8.

---

## Checkpoint 4 -- #259, morph bundle inflection class (NEXT)

- [ ] **T4.1 (C10)** Implement the navigation helper once
      (`bundle.MsaRA` -> null check -> `cast_to_concrete` -> narrow to
      `IMoStemMsa` -> `.InflectionClassRA`), then route
      `WfiMorphBundleOperations.py:1261` (`GetInflectionClass`) through it.
      Returns `None` for a null MSA or a non-stem subtype -- never raises.
- [ ] **T4.2 (C10)** Fix the three silent copy loops:
      `WfiMorphBundleOperations.py:335,336` (`Duplicate`),
      `WfiAnalysisOperations.py:589,590`, `WordformOperations.py:878,879`.
      A copied bundle must carry its inflection class where the source's MSA
      is a stem MSA.
- [ ] **T4.3 (C10)** Fix `GetSyncableProperties` at `:385,386` so the key
      appears with a real value instead of being silently absent.
- [ ] **T4.4 (Q2, gates C11)** Live: count how many Sena 3 morph bundles
      share an MSA with at least one other bundle. Feed that number to a
      domain ruling on `SetInflectionClass` semantics (refuse / warn /
      accept). **Do not implement the write path before the ruling.**
      -> `evidence/live-T4.4-msa-sharing.md`.
- [ ] **T4.5 [B on Q2]** Implement `SetInflectionClass:1313` per the T4.4
      ruling.
- [ ] **T4.6** Update the docstrings/See-Also at
      `WfiMorphBundleOperations.py:289,367,1157,1200,1223,1240,1256,1264,
      1282,1284,1287,1297`, `WordformOperations.py:785`, and
      `docs/FUNCTION_REFERENCE.md:57-58`. Leave
      `Grammar/POSOperations.py:783-854` alone (`InflectionClassesOC` is
      real).
- [ ] **T4.7** Live verification with pre/post re-read by HVO, on
      `target_sandbox` for writes and `sena3_sandbox` for the subtype-mix
      read path (it needs the 1144-bundle non-stem population).
      -> `evidence/live-T4-inflclass.md`.
- [ ] **T4.8** Commit and push.

**Checkpoint:** the loud path stops raising, the three silent drops stop
dropping, and the write path is either implemented under a ruling or
explicitly deferred with the reason recorded.

---

## Checkpoints 5-7 -- #303/#309, `Lists/OverlayOperations.py` (C12)

Follow `reviews/cycle1-domain.md` sections 2-5 verbatim.

**Checkpoint 5 (domain spurt A) -- re-root + core CRUD**
- [ ] **T5.1** Drop the `PossibilityItemOperations` base; inherit
      `BaseOperations` directly. Remove the `_get_list_object` stub (#309).
- [ ] **T5.2** Rewrite against `ILangProject.OverlaysOC`:
      `GetAll/Create/Delete/Duplicate/Find/Exists/GetName/SetName/CompareTo/
      GetSyncableProperties`. `Name` is a plain `System.String` -- direct
      assignment, **no `wsHandle` parameter**, no `CopyAlternatives`.
      `Create` requires a non-null `poss_list` for `PossListRA` and raises
      `FP_ParameterError` if omitted. `GetGuid` stays as-is.
- [ ] **T5.3** Live-verify writes on `target_sandbox`, reads on
      `sena3_sandbox` (reuse the #277 evidence fixtures).
      -> `evidence/live-T5-overlay-crud.md`.

**Checkpoint 6 (domain spurt B) -- deletions + `PossItemsRC` write surface**
- [ ] **T6.1** Delete the 10 dead methods: `GetDescription`,
      `SetDescription`, `IsVisible`, `SetVisible`, `GetDisplayOrder`,
      `SetDisplayOrder`, `GetElements`, `AddElement`, `RemoveElement`,
      `GetChart`, `FindByChart`, `GetVisibleOverlays` (per the domain
      table). **No raising stubs, no deprecation shim.** `GetPossItems`
      is untouchable.
- [ ] **T6.2** Add the missing write surface: `SetPossList`, `AddPossItem`,
      `RemovePossItem` -- `PossListRA`/`PossItemsRC` are currently
      read-only, and `AddElement`/`RemoveElement` are being deleted without
      a replacement otherwise.
- [ ] **T6.3** Live-verify on `target_sandbox`.
      -> `evidence/live-T6-overlay-writes.md`.

**Checkpoint 7 (domain spurt C) -- docs, stubs, tests**
- [ ] **T7.1** Rewrite `Lists/OverlayOperations.pyi` (it already disagrees
      with the source: it declares `BaseOperations[Any]` while the source
      says `PossibilityItemOperations` -- after T5.1 the stub becomes
      accidentally correct on that point, but the signatures still need
      work).
- [ ] **T7.2** New Category-10-style entry in
      `docs/API_ISSUES_CATEGORIZED.md` with an old-API/new-API migration
      table and a "why removed" note.
- [ ] **T7.3** Update `docs/FUNCTION_REFERENCE.md:905-951` (14 entries,
      several documenting parameters the real class never took),
      `docs/MIGRATION_GUIDE.md:168,173`,
      `docs/sphinx/api/flexicon.code.Lists.rst:31`, the class docstring and
      usage example, and `FLExProject.py:3030-3057` (whose docstring
      currently comments the examples out as "currently broken").
- [ ] **T7.4** Rewrite `examples/lists_overlay_operations_demo.py` -- the
      entire demo exercises the non-functional inherited CRUD.
- [ ] **T7.5** Rewrite `tests/operations/test_overlay_operations.py` for the
      new shape, preserving the 3 passing `GetPossItems` live tests.
- [ ] **T7.6** Commit and push.

---

## Checkpoint 8 -- campaign close

- [ ] **T8.1** CHANGELOG entries for all six issues, plus the C7 inert-`deep`
      note and the C12 breaking-change note.
- [ ] **T8.2 (C1)** Record the surviving notebook-ownership form in
      `docs/API_ISSUES_CATEGORIZED.md` as the named house pattern, so it is
      a precedent rather than a lone call site.
- [ ] **T8.3 (C5, LOW -- droppable)** Mock-fidelity ratchet: cross-reference
      LCM member names asserted by test doubles against the 4096-name
      snapshot, so no future hand-rolled mock can invent a member the way
      `_MockRepository` invented `RecordsOC`.
- [ ] **T8.4** Present `proposed-issues.md` to the user for approval
      (`needs_human`); file on approval with `gh`.
- [ ] **T8.5** Final crew gate: verification + QC + domain on the whole
      campaign diff, then the lead's approval report.
- [ ] **T8.6 (#283 follow-up, from the cycle-3 domain ruling Q-B)**
      Delete-survival regression test: `Duplicate` an environment that has
      a `LeftContextRA`, then `envs.Delete(duplicate)`, then re-read the
      **source** by HVO and assert its `LeftContextRA` still resolves
      non-null. Live, `sena3_sandbox` (same phoneme-inventory reason as
      T3.5(a)). Rationale for deferring rather than folding into spurt 3:
      the risk is unrealized in the shipped diff -- `Delete` (`:195-233`)
      only calls `phon_data.EnvironmentsOS.Remove(env)` and never touches
      `ContextsOS`, so it cannot cascade-delete a still-referenced context.
      The gap is missing *coverage* of the highest-risk regression path,
      not a live defect. Do not let checkpoint 8 close with T8.6 open.
