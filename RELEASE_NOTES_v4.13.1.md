# pyflexicon 4.13.1

**Released 2026-11-02** | `pip install --upgrade pyflexicon`

A patch release that fixes a class of silent failures: pythonnet can hand back
bare interface views from FLEx collections, and a lookup by Python identity
(`IndexOf`, `Remove`, `in`, `MoveTo`) then misses the object you hold. About
90 operations now match by HVO. The HVO sweep changed no signature. **Four
breaking changes**, all to methods that never worked as documented -- see
`docs/MIGRATION_GUIDE.md`:

- #828: `Pronunciations.AddMediaFile` now returns an `ICmMedia` (use
  `.MediaFileRA` for the `ICmFile`), and `RemoveMediaFile` raises
  `FP_ParameterError` instead of returning silently.
- #830: `Allomorphs` inflection-class methods now act on affix allomorphs
  only; on stem allomorphs they return `[]` or raise `FP_ParameterError`.
- #831: the `Examples` media methods are deprecated (removal in 5.0); the
  writers now raise and the readers return `[]` / `0`.
- #832: `ConstChartClauseMarkers.AddDependentClause` / `InsertDependentClause`
  take a chart row, not a marker; the parameter is renamed `row_or_hvo`.

---

## What changed for you

- **`Delete`** on senses, examples, pronunciations, etymologies, allomorphs,
  lexical references, variants, parts of speech, phonemes, natural classes,
  environments, strata, morph rules, features, texts and analyses, notebook
  records, people, locations, possibility lists and items, overlays, agents and
  discourse charts now removes the right object instead of doing nothing or
  raising.
- **`Reorder` / `Move*`**, **Add/Remove on reference collections**, and
  **`Duplicate(insert_after=...)`** get the same fix.
- **`GetBestString`** accepts live multistrings (issue 640).
- **Pronunciation media** (`AddMediaFile`, `MoveMediaFile`, `RemoveMediaFile`
  and deep `Duplicate`, including `LexEntry` deep `Duplicate`) now works on
  `ICmMedia`, the real element type of `MediaFilesOS` (#828).
  **`AddMediaFile` now returns an `ICmMedia`**; use `.MediaFileRA` to get the
  `ICmFile`. `RemoveMediaFile` and `MoveMediaFile` also accept an `ICmFile` or
  HVO.
- **`LexReferences.GetAll`** no longer raises: it works project-wide, per sense
  and per entry (#829).
- **Allomorph inflection classes** (`GetInflectionClasses`,
  `AddInflectionClass`, `RemoveInflectionClass`) now use the affix allomorph's
  `InflectionClassesRC`, the only place it exists. For a stem, use
  `project.MSA.SetInflectionClass(msa, infl_class)` (#830).
- **`Examples` media methods** (`GetMediaFiles`, `GetMediaCount`,
  `AddMediaFile`, `RemoveMediaFile`, `MoveMediaFile`) are deprecated. An example
  sentence has no media collection; its audio appears to be a file name in
  the audio writing-system alternative (observed in surveyed projects; not yet
  exercised by flexicon tests). Purpose-built
  methods are planned for 4.14.0 (#831).
- **Dependent clauses** take an `IConstChartRow` or its HVO (#832). These methods
  write only `DependentClausesRS`; FLEx also sets the row's clause type and
  group flags, and a helper for that is planned for 4.14.0.

`CHANGELOG.md`, section `[4.13.1]`, has the full list.

---

## Verification

From `specs/4.13.1-release-gate/evidence/live-full-sweep-cycle6.md`:

- Offline: 4006 passed, 0 failed.
- Live (`run_mode` live, `FLEXLIBS_REQUIRE_LIVE=1`, sandbox fixtures): 127
  passed, 0 failed, 0 skipped of 127 collected, across the 99 live test files
  changed since v4.13.0. Not every live test in the repository was run.
- Verified offline only: `MoAffixProcess` handling for #830 (the test project
  has none).
- #831 is verified as inert (no file or text change); the audio writing-system
  route was not exercised because no fixture has an audio writing system.

## Known gaps

- The FLEx user-interface label for affix-allomorph inflection classes was not
  verified.
- `cast_to_concrete` returns a bare `ICmObject` for `CmMedia` (#836, open).
