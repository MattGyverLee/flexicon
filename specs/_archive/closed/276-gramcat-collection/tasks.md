# Issue #276 -- tasks

Dependency order. T2 before T4 (the backfill must exist before GramCat
delegates to it). T7/T8/T9 must land in the SAME commit as T4 -- the
pinning test fails by design the moment GetAll is repointed.

## Phase 1 -- decision record

- [x] **T1** Record the ruling. `evidence/domain-ruling.md`,
      `evidence/code-survey.md`, `spec.md`. Includes the verified
      correction to the ruling's `GetParent`/`parent=` assumption.

## Phase 2 -- code

- [x] **T2** Backfill `POSOperations.GetParent(pos_or_hvo)`.
      Return the owning `IPartOfSpeech` for a subcategory, `None` for a
      top-level POS (owner is the `PartsOfSpeechOA` list, not a
      possibility). Do NOT copy `GramCatOperations.GetParent` verbatim:
      it catches `System.InvalidCastException` at
      `GramCatOperations.py:441` while never importing `System` in that
      module, so its except clause would raise `NameError` if ever
      reached. Add to `POSOperations.pyi`. Unit test + live coverage.

- [x] **T3** `FLExProject.GramCat` -> `return self.POS`.
      Rewrite the docstring per spec section 5: category inventory vs
      sense-level MSA vs feature side, with the three pointers. Model it
      on the `Features` alias at `FLExProject.py:1681`. Drop the
      `_gramcat_ops` cache attribute.

- [x] **T4** Retire the TypesOC implementation in `GramCatOperations`.
      Class becomes a thin deprecated subclass of `POSOperations`
      emitting `DeprecationWarning` on construction. Delete `GetAll`,
      `Delete`, `GetSubcategories`, `GetParent`, `Duplicate`,
      `__DuplicateSubcategory`, `GetName`, `SetName`,
      `GetSyncableProperties`, `CompareTo`, `_GetSequence`,
      `__ResolveObject`, `__WSHandle` -- all inherited correctly from
      `POSOperations`. Keep `Create` as an override that raises
      `FP_ParameterError` naming `project.POS.Create(name, abbreviation)`
      and `project.POS.AddSubcategory(parent, name, abbreviation)`.
      Drop the now-unused `IFsFeatStrucTypeFactory` /
      `ICmPossibilityFactory` / `ICmPossibility` imports.

- [x] **T5** Fix `GramCatOperations.pyi`. It currently declares `Find`
      and `Exists`, which the `.py` never defined -- the stub advertised
      a surface that raised `AttributeError`. Reduce to the deprecated
      subclass shape.

- [x] **T6** Fix the three false docstrings that call the
      never-implemented `project.GramCat.Find("Verb")`:
      `FLExProject.py:1876,1880-1881` and
      `Lexicon/MSAOperations.py:141,145-146`. Change to
      `project.POS.Find("Verb")`, matching the spelling
      `LexSenseOperations.GetPartOfSpeechObject` already uses.

## Phase 3 -- tests (same commit as T4)

- [x] **T7** Update `tests/operations/test_collection_cast_pattern.py`.
      - `TestGramCatGetAllRecursionClaim` (:836): KEEP
        `test_fsfeatstructype_has_no_subpossibilities` -- the LCM
        baseline fact is still true and still worth pinning. REPLACE
        `test_getall_recursion_is_documented_as_unreachable` (:872),
        which asserts `"MsFeatureSystemOA" in` GetAll's source and so
        fails by design once T4 lands. Its successor should pin the
        resolution: GramCat no longer reads the feature system, and
        `project.GramCat` is the POS list. Rewrite the class docstring
        to record the ruling rather than the open question.
      - Parametrized row at :712-714 (`GramCatOperations.GetSubcategories`
        / `SubPossibilitiesOS`): the method is gone from the class;
        repoint at `POSOperations.GetSubcategories`, or drop it if that
        is already covered there.

- [x] **T8** Retire `tests/operations/test_gramcat_duplicate.py`.
      It is mock-only, never imports the real class, and asserts on
      `_simulate_*` reimplementations of the TypesOC path that T4
      deletes. Its #163 lesson (an OC takes `Add`, not
      `IndexOf`/`Insert`) belongs with a site that still has an OC.
      Delete it -- but confirm #163 retains coverage elsewhere first.

- [x] **T9** Regenerate `tests/contract/snapshots/expected_contract.json`.
      The `code/Grammar/GramCatOperations.py` entry records
      `ICmPossibility`, `ICmPossibilityFactory`, `IFsFeatStrucTypeFactory`,
      `ITsString` and `TsStringUtils` -- all dropped by T4.

- [x] **T10** Confirm the survivors need no change:
      `tests/phase2_validation_tests.py:664` (only exercises
      `_EnsureWriteEnabled` / `_ValidateParam`, should pass unchanged),
      `tests/test_operations_baseline.py:79` and
      `tests/conftest.py:162,743` (import by name -- fine, T4 keeps the
      symbol).

## Phase 4 -- live verification (MANDATORY, blocks approval)

- [x] **T11** Live LCM verification on the **Target** project.
      The write path changed (Create now raises; Delete and Duplicate
      now address `PartsOfSpeechOA`), so `CLAUDE.md`'s live rule applies.

      Invocation:

          python scripts/restore_target.py
          $env:FLEXLIBS_REQUIRE_LIVE = "1"
          python -m pytest tests/operations/test_276_gramcat_pos_alias.py -m requires_live_project -q

      Must demonstrate, with values **re-read from the LCM after the
      write** rather than asserted on inputs:

      1. `project.GramCat is project.POS`.
      2. `GramCat.GetAll()` yields `IPartOfSpeech`, and `recursive=True`
         actually descends -- strictly more results than
         `recursive=False` on a project with nested categories. Use
         Sena 3 if the Target is too bare; record which was used.
      3. `POS.GetParent(subcat)` round-trips against
         `POS.AddSubcategory`, and returns `None` for a top-level POS.
      4. `GramCat.Create(...)` raises `FP_ParameterError` and writes
         NOTHING -- `MsFeatureSystemOA.TypesOC.Count` identical before
         and after. This is the regression that matters most, since it
         is the behaviour that corrupted feature systems.

      Evidence -> `evidence/live-T11.md`: exact command, the `run_mode`
      value from `tests/live_status.json`, pre-state and post-state, and
      the pass/fail line. `run_mode: "mock"` proves nothing and must be
      reported as `FAIL: unverified`.

## Phase 5 -- docs

- [x] **T12** Documentation.
      - `docs/MIGRATION_GUIDE.md`: a prominent entry. `project.GramCat`
        now means the POS list; `GetAll` / `GetName` /
        `GetSubcategories` return POS data, not feature types;
        `GramCat.Create` raises with a pointer. Anyone who wanted
        `TypesOC` wants `project.InflectionFeatures.TypeFind` /
        `TypeCreate`; anyone who wanted the sense-level composite wants
        `project.Senses.GetGrammaticalInfo`. Include the ruling's Q4
        note: projects that called `GramCat.Create` have stray entries
        to hand-clean in Grammar > Features, no automatic cleanup is
        offered, and none should be attempted.
      - `CHANGELOG.md`: breaking-change entry, following the
        `docs/_templates/CHANGELOG_ENTRY.md` shape used for the
        `flat=` / `recursive=` rename.
      - `docs/API_ISSUES_CATEGORIZED.md:693`: the "Site 4 /
        GramCatOperations / TypesOC (Duplicate)" row is moot once the
        branch is deleted. Annotate it rather than silently dropping it,
        and fix the note at :703 that describes it.
      - Regenerate `examples/grammar_gramcat_operations_demo.py` --
        `:89` calls `project.GramCat.Create(test_name)`, which now
        raises.

- [x] **T13** File the two out-of-scope follow-ups:
      1. Migration/cleanup *guidance* for stray `IFsFeatStrucType`s
         (documentation only -- ruling Q4 forbids an auto-migration).
      2. Whether `POSOperations` should expose
         `IPartOfSpeech.DefaultFeaturesOA` / `InherFeatValOA`
         (ruling Q5).

## Commit-message hazard

Per `CLAUDE.md`: this work genuinely resolves #276, so a `closes #276`
footer or subject parenthetical is correct and intended. Do NOT write
prose like "close #276's data-model question" -- the possessive form
fires the keyword and the `commit-msg` hook will block it. Enable the
hook once per clone: `git config core.hooksPath .githooks`.
