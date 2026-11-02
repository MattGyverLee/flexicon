# pyflexicon 4.13.1

**Released 2026-11-01** | `pip install --upgrade pyflexicon`

A patch release that fixes a class of silent failures: pythonnet can hand back
bare interface views from FLEx collections, and a lookup by Python identity
(`IndexOf`, `Remove`, `in`, `MoveTo`) then misses the object you hold. About
90 operations now match by HVO. **No breaking changes**; no signature changed.

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

`CHANGELOG.md`, section `[4.13.1]`, has the full list.

---

## Known gaps

- Issue 740 (`Allomorph` reference-collection membership) was verified offline
  only; no live run was recorded for it.
