# pyflexicon 4.13.1

**Released 2026-11-01** | `pip install --upgrade pyflexicon`

A patch release that fixes a class of silent failures: pythonnet can hand back
bare interface views from FLEx collections, and a lookup by Python identity
(`IndexOf`, `Remove`, `in`, `MoveTo`) then misses the object you hold. About
90 operations now match by HVO. No signature changed. **One breaking change**
(#828): `Pronunciations.AddMediaFile` now returns an `ICmMedia` (use
`.MediaFileRA` for the `ICmFile`), and `RemoveMediaFile` raises
`FP_ParameterError` instead of returning silently -- see
`docs/MIGRATION_GUIDE.md`.

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

`CHANGELOG.md`, section `[4.13.1]`, has the full list.

---

## Known gaps

- Issue 740 (`Allomorph` reference-collection membership) was verified offline
  only; no live run was recorded for it.
