# T2a Implementation Evidence -- Issue #325 Syncable Properties

**Task:** T2a (implement R1, R2, R6 on EtymologyOperations + LexEntry Duplicate site)
**Branch:** fix/325-syncable-properties
**Working directory:** C:/Github/flexicon-325
**Date:** 2026-09-22
**Rulings applied:** R1, R2, R6 (from specs/325-syncable-properties/rulings.md)
**Breaking-change review:** specs/325-syncable-properties/evidence/T1b-breaking-changes.md

---

## Offline gate

```powershell
cd C:\Github\flexicon-325
python -m pytest -m "not requires_live_project" -q
```

Result:
```
5 failed, 2031 passed, 899 deselected, 17 warnings in 10.10s
```

Pre-existing failures (same as T0 baseline):
- tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies
- tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline
- tests/operations/test_issue266_phoneme_ws_resolution.py::TestApplyBasicIPASymbolSharedIndexCache::test_fresh_index_cache_per_apply_call
- tests/operations/test_issue267_translations_ws_resolution.py::TestTranslationsOCSharedIndexCache::test_fresh_index_cache_per_apply_call
- tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations

No new failures introduced. 2031 passed (unchanged from baseline).

**Live verification:** T2a-specific live run was not repeated after T2a landed;
campaign **T3** live evidence supersedes the unverified note for the #325
wave-1 write path. See
`specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`
(`run_mode`: live, etymology language_rs / Duplicate / deprecated language
APIs, lex reference owner_guid, media_uris, lex sense R7, and related checks).

---

## Files changed

### flexicon/code/Lexicon/EtymologyOperations.py

**R2 -- Remove LanguageNotesRA from Duplicate docstring:**
- Line ~334: Replaced "Reference properties copied: LanguageNotesRA" with a note
  that LanguageRS is not copied by Duplicate; use SetLanguages() afterward.

**R2 -- Remove LanguageNotesRA block from Duplicate body:**
- Lines ~387-389: Removed the dead `if hasattr(source, "LanguageNotesRA")` block.
  LanguageNotesRA does not exist on ILexEtymology (live-T0-etymology-raw.json).

**R1 -- Replace LanguageRA+LanguageNotesRA with language_rs in GetSyncableProperties:**
- Lines ~476-494 replaced: `"LanguageRA"` (atomic GUID or None, permanent no-op)
  and `"LanguageNotesRA"` (always None, permanent no-op) removed.
- New key `"language_rs"`: `[str(lang.Guid) for lang in item.LanguageRS]` with
  `hasattr(item, "LanguageRS")` guard (LanguageRS is on concrete impl, not interface).
  Returns `[]` when absent.

**R1 -- Update ApplySyncableProperties:**
- Docstring updated: removed LanguageRA/LanguageNotesRA references; documented
  language_rs replace-whole-sequence semantics.
- Removed `_ra_fields` tuple and `ra_props` dict (no RA fields remain).
- Added `language_rs` handler: dispatches on `k == "language_rs"` key; uses
  `hasattr(item, "LanguageRS")` guard; implements replace-whole-sequence with
  `fill_gaps` unit = entire sequence; warns+skips unresolved GUIDs.

**R6 -- Add GetLanguages/SetLanguages (primary):**
- `GetLanguages(etymology_or_hvo)` -> `list[ICmPossibility]`: accesses
  `LanguageRS` via `hasattr` guard; returns `[]` if absent.
- `SetLanguages(etymology_or_hvo, languages)`: replaces entire LanguageRS
  sequence; requires write enabled; warns+returns if `LanguageRS` absent.

**R6 -- Deprecate GetLanguage/SetLanguage (index-0 wrappers):**
- `GetLanguage(etymology)`: emits `[WARN] GetLanguage reads index 0 of LanguageRS
  (a sequence); use GetLanguages() for the full list.` and delegates to
  `GetLanguages()[0]` or None.
- `SetLanguage(etymology, language)`: emits `[WARN] SetLanguage sets only index 0
  of LanguageRS (a sequence, not atomic); use SetLanguages() to set the full
  sequence.` and delegates to `SetLanguages([language])` or `SetLanguages([])`.

### flexicon/code/Lexicon/LexEntryOperations.py

**R2 -- Remove LanguageNotesRA from Duplicate (etymology branch):**
- Lines ~482-483: Removed `if hasattr(etymology, "LanguageNotesRA") and
  etymology.LanguageNotesRA: new_etym.LanguageNotesRA = etymology.LanguageNotesRA`.
  Dead block (field never existed on ILexEtymology).

---

## Test constraints honored

- `tests/operations/test_lexicon_brackets_live.py::test_setlanguage_persists_to_the_lcm`
  left untouched (still xfail(strict=True) with LanguageRA assertion). T6 rewrites it.
- DoNotShowMainEntryInRC references in LexEntryOperations.py NOT touched (R7 scoped
  to LexSenseOperations only; T1b scoping constraint).

---

## Verification status

**PASS (via T3)** -- write-path behavior for T2a rulings (R1, R2, R6) is covered
by `tests/operations/test_325_syncable_properties_live.py` and documented in
`specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`
(`run_mode`: live). No separate T2a-only live artifact is required for T4 QC
once `pattern-audit.md` is present.
