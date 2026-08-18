# Live LCM evidence — closing the last 4 red tests before 4.4.1

**Task:** Fix the four live tests that have been failing since before the
4.4.0 release:

- `tests/operations/test_phonemes.py::TestPhonemeSync::test_getsyncable_surfaces_feature_specs`
- `tests/operations/test_phonemes.py::TestPhonemeSync::test_apply_rewires_feature_specs`
- `tests/operations/test_apply_syncable_properties.py::TestApplySyncablePropertiesLive::test_etymology_source_multistring_roundtrip`
- `tests/operations/test_apply_syncable_properties.py::TestApplySyncablePropertiesLive::test_pronunciation_form_roundtrip`

**Projects:** Sena 3 (both suites' `writable_project` module fixture opens
"Sena 3" first), Target (bracket-regression check).
**Date:** 2026-08-18

---

## 1. Reproduction (before fix)

```powershell
python scripts/restore_target.py
python scripts/restore_sena3.py
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phonemes.py tests/operations/test_apply_syncable_properties.py -m requires_live_project -q -p no:cacheprovider -rf --tb=short
```

**Result (before):** `4 failed, 16 passed, 38 deselected in 7.43s`

Failures:

1. `test_getsyncable_surfaces_feature_specs` — `StopIteration`
2. `test_apply_rewires_feature_specs` — `StopIteration`
3. `test_etymology_source_multistring_roundtrip` — `AttributeError: 'ILexEtymology' object has no attribute 'Source'`
4. `test_pronunciation_form_roundtrip` — `TypeError: 'set' object is not subscriptable`

## 2. Root causes

### 1 & 2 — `StopIteration` on `feat_ops.GetValues(feat)` filtered by `GetAbbreviation(v) == "+"`

Not a missing-data skip; a wrong-place finder. `PHON:fPAConsonantal`'s
catalog source (`PhonFeatsEticGlossList.xml`) only ever writes `Abbreviation`
text into the **"en"** writing system. `GetAbbreviation(v)` with no explicit
`wsHandle` defaults to the *project's* default analysis WS. Sena 3's default
analysis WS is **"pt"** (Portuguese), not "en", so the abbreviation read
back empty for every value, and `next(...)` found nothing.

Verified live via debug script against a freshly-restored Sena 3:

```
DefaultAnalWs handle: 999000004     (pt)
value guid ec5800b4-... abbrev(default)= ''      abbrev(en)= '+'
value guid 81c50b82-... abbrev(default)= ''      abbrev(en)= '-'
```

Against Target (default analysis WS = "en") the same lookup returns `'+'`/`'-'`
immediately — confirming the failure is WS-dependent, not a project-data gap.

**Fix (test-only):** `tests/operations/test_phonemes.py` now matches the
"+" value by its canonical, WS-independent catalog GUID
(`ec5800b4-52a8-4859-a976-f3005c53bd5f`, the same constant already used as
`CONSONANTAL_POSITIVE_VALUE_GUID` in `tests/operations/test_phon_features.py`)
instead of a `GetAbbreviation()` call with no WS override. No production
code was at fault — the catalog import writes "en" by design, and
`GetAbbreviation()` correctly defaults to the project's own analysis WS for
non-catalog callers.

### 3 — `ILexEtymology` has no `Source` field (production bug, fixed)

`EtymologyOperations.Create(source=...)` called
`new_etymology.Source.set_String(...)`. Live reflection (`dir()` on a
freshly-created, owned `ILexEtymology` in Sena 3) confirms `Source` **does
not exist on the installed LCM at all** — not renamed, not retyped, gone.
This matches the pre-existing STRONG LEAD from a 4.4.0 investigation
(`EtymologyOperations.Duplicate()`, commit 3da12cf, already `hasattr`-guarded
this for exactly this reason) and an existing `xfail(strict=True)` test in
`tests/operations/test_lexicon_brackets_live.py::TestEtymologyBrackets::test_setsource_round_trips_through_lcm`.

Full live member dump of `ILexEtymology` (Sena 3, `factory.Create()` +
`EtymologyOS.Add()`):

```
... Bibliography Comment Form Gloss Guid Hvo ...
LanguageNotes  LanguageRS  LiftResidue  Note ...
```

Follow-up reflection:

```
LanguageNotes type: <class 'SIL.LCModel.IMultiString'>
LanguageRS   type: <class 'SIL.LCModel.ILcmReferenceSequence[ICmPossibility]'>
```

Cross-checked against `Language Explorer/Configuration/Parts/LexEntryParts.xml`:
the UI's "Source Language Notes" slice binds `field="LanguageNotes"`
(`editor="multistring"`), and "Source Language" binds `field="Language"`
(C# property `LanguageRS`, `editor="possVectorReference"` onto the
Languages list) — a *new*, separate, controlled-vocabulary concept, not a
retyped `Source`.

**Fix (production):** `flexicon/code/Lexicon/EtymologyOperations.py` —
`Create(source=...)`, `GetSource()`, `SetSource()`,
`GetSyncableProperties()`, and `ApplySyncableProperties()` now all
read/write `LanguageNotes` (`IMultiString`) instead of the nonexistent
`Source`. The public method names, the `source=` kwarg, and the `"Source"`
key in the syncable-properties dict are all kept unchanged for API
stability — only the LCM field they resolve to changed.
`Duplicate()`'s dead `hasattr(duplicate, "Source")` guard (which could never
fire, since `Source` never exists) was replaced with an unconditional
`duplicate.LanguageNotes.CopyAlternatives(source.LanguageNotes)` — this was
previously silent data loss on duplicate for any etymology with source-
language-notes text, now fixed. `GetLanguage`/`SetLanguage` (which use the
equally-nonexistent `LanguageRA`, silently no-opping) were deliberately
**left untouched** — a different, pre-existing, already-`xfail`-documented
bug (`test_setlanguage_persists_to_the_lcm`), out of scope for this task.

Docs corrected to match (both were stale on this point):
- `CLAUDE.md` — "Same-name fields can have different LCM types" bullet.
- `docs/API_ISSUES_CATEGORIZED.md` — Category 8 table and prose (new
  "CORRECTED 2026-08-18" subsection).
- `tests/operations/test_etymologies_live.py` header comment.

Corollary: `tests/operations/test_lexicon_brackets_live.py::TestEtymologyBrackets::test_setsource_round_trips_through_lcm`
was `xfail(strict=True, raises=AttributeError)` — now that `SetSource`/
`GetSource` work, that test would XPASS (strict → hard failure). The
`xfail` marker was removed and the test now asserts the fixed behaviour
directly (verified green below).

### 4 — `GetAllVernacularWSs()` / `GetAllAnalysisWSs()` return a `set` (test bug)

Both methods are documented (`FLExProject.py`) as returning "a set of
language tags"; they always have. `test_pronunciation_form_roundtrip` and
`test_etymology_source_multistring_roundtrip` both indexed the result with
`[0]`, which only works by accident on some Python set iteration orders and
raises `TypeError` in general. Separately, even if indexing worked, an
*arbitrary* member of the set would not necessarily be the writing system
`Pronunciation.Create()` / `Etymology.Create()` actually wrote the seed
value to (both default to the project's *default* vernacular/analysis WS
respectively) — a single-key round-trip assertion would then intermittently
see two WS alternatives instead of one. Both tests carry the comment "these
are authored but NOT executed by this task's author in the authoring
environment", which explains how this shipped.

**Fix (test-only):** both tests now call `GetDefaultAnalysisWS()` /
`GetDefaultVernacularWS()` (existing `FLExProject` methods returning
`(language_tag, display_name)`) and use `[0]` on that *tuple*, which
deterministically matches the WS the preceding `Create()` call wrote to.

## 3. Verification (after fix)

```powershell
python scripts/restore_target.py
python scripts/restore_sena3.py
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phonemes.py tests/operations/test_apply_syncable_properties.py -m requires_live_project -q -p no:cacheprovider -rf --tb=short
```

**Result (after):** `20 passed, 38 deselected in 8.64s`

`tests/live_status.json` → `"run_mode": "live"`.

## 4. Regression check on the EtymologyOperations.py change

Ran every live suite that touches `EtymologyOperations` (fresh
Target + Sena 3 restore beforehand):

```powershell
python -m pytest tests/operations/test_etymologies_live.py tests/operations/test_lexicon_brackets_live.py tests/operations/test_owner_cast_pattern.py tests/operations/test_undoable_mode_live.py "flexicon/sync/tests/test_duplicate_operations.py::TestEtymologyDuplicate" -m requires_live_project -q -p no:cacheprovider -rf --tb=short
```

**Result:** `71 passed, 24 deselected, 2 xfailed` (the 2 xfails are the
pre-existing, unrelated, and still-correct
`TestEtymologyBrackets::test_setlanguage_persists_to_the_lcm` xfail plus
one other unrelated pre-existing xfail in the same file).

Before this change, the same run was `70 passed, 1 failed (XPASS strict:
test_setsource_round_trips_through_lcm), 24 deselected, 1 xfailed` —
confirming the `SetSource`/`GetSource` fix flipped that xfail to a real
pass, and the marker update reflects that correctly.

## 5. Offline suite (unaffected by any of the above)

```powershell
python -m pytest -m "not requires_live_project" -q -p no:cacheprovider
```

**Result:** `1461 passed` (see terminal output captured during this task;
no change in count — all touched files are in the `requires_live_project`
live suite only).
