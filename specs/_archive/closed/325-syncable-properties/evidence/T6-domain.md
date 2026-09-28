# T6 -- Domain conformance review (issue #325)

**Task:** T6 (lex-domain)
**Date:** 2026-09-22
**Worktree:** `C:/Github/flexicon-325` (branch `fix/325-syncable-properties`)
**Authority:** `specs/325-syncable-properties/rulings.md` (R1-R8)
**Evidence reviewed:** worktree Operations code + `specs/325-syncable-properties/evidence/live-T3-syncable-properties.md` (`run_mode`: live)

**Scope notes (binding for this review):**

- R4 live media round-trip remains **unverified** (`needs_human`); does not downgrade code-shape conformance when `Name` (R8) and payload/access path match the ruling.
- R7 applies to **LexSenseOperations** only; **LexEntryOperations** `DoNotShowMainEntryInRC` was intentionally left unchanged (T1b scope boundary).
- R5 gap handling: **choice (a)** (#290 model + `# VERIFY in T3`; full Preposed proof deferred to T3). T3 section (d) now **PASS** on the full path.
- T6 rewrite: `test_setlanguage_persists_to_the_lcm` updated from obsolete `LanguageRA` xfail to `LanguageRS` / `SetLanguages` (R6).

---

## Verdict summary

| Ruling | Verdict | One-line basis |
|--------|---------|----------------|
| R1 | **CONFORM** | `language_rs` GUID list, replace apply, fill_gaps on sequence, warnings on unresolved; no `LanguageRA` in sync paths |
| R2 | **CONFORM** | `LanguageNotesRA` removed from etymology sync/Duplicate; `"Source"` <- `LanguageNotes`; LexEntry duplicate site clean |
| R3 | **CONFORM** | `owner_guid` + `targets_rs`; `ReferenceTypeRA` gone; re-parent = warn, no Owner assign |
| R4 | **CONFORM** | Code shape matches ruling; **live media_uris end-to-end unverified** (T3 FAIL, needs_human) |
| R5 | **CONFORM** | `row.CellsOS` insert; WordGroupRA/ColumnRA before Preposed; choice (a); T3 (d) PASS |
| R6 | **CONFORM** | `GetLanguages`/`SetLanguages`; deprecated singular methods warn + delegate; bracket test rewritten |
| R7 | **CONFORM** | `DoNotShowMainEntryInRC` absent from LexSense sync/apply; T3 (e) PASS; LexEntry untouched |
| R8 | **CONFORM** | `Name` in Get/Apply sync; docstring lists Name; T3 (c) Name PASS |

**Campaign domain gate:** **CONFORM** on R1-R3, R5-R8. R4 implementation **CONFORM**; R4 live verification **DIVERGE** from "verified" bar until a media-populated project is exercised (documented gap, non-blocking per campaign brief).

---

## R1 -- ILexEtymology LanguageRS

**Code:** `flexicon/code/Lexicon/EtymologyOperations.py`

- `GetSyncableProperties`: emits `language_rs` as ordered `[str(lang.Guid) for lang in item.LanguageRS]` with `hasattr(item, "LanguageRS")`; empty list when absent (lines 472-480).
- `ApplySyncableProperties`: extracts `language_rs`, maps `"Source"` -> `LanguageNotes`; replace via `Clear()` + `Add()`; `fill_gaps` skips when `item.LanguageRS.Count > 0` (529-547).
- Unresolved GUID: `[WARN] ... language_rs GUID ... not found ... skipped` (543-546) -- policy matches ruling (warn, skip, no raise).
- Sync paths: no `LanguageRA` in `flexicon/` (only historical mentions in Get/SetLanguage docstrings).

**T3:** Section (a) PASS -- `language_rs` in payload, `LanguageNotesRA absent`; LanguageRS apply skipped only because Languages list empty in Target (documented), not a code defect.

**Verdict:** **CONFORM**

---

## R2 -- Drop LanguageNotesRA

**Code:**

- No `LanguageNotesRA` in `GetSyncableProperties` or `ApplySyncableProperties` (no `_ra_fields` remnant).
- `Duplicate`: copies `LanguageNotes` via `CopyAlternatives`; docstring notes LanguageRS not copied; no `LanguageNotesRA` block (329-385).
- `LexEntryOperations.py`: no `LanguageNotesRA` references (grep clean).

**T3:** `(a) LanguageNotesRA absent` True; Duplicate LanguageNotes `T3_source_note` PASS.

**Verdict:** **CONFORM**

---

## R3 -- LexReference owner_guid + targets_rs

**Code:** `flexicon/code/Lexicon/LexReferenceOperations.py`

- Payload: `owner_guid` from `ILexRefType(item.Owner).Guid`; `targets_rs` ordered GUID list (1337-1348).
- No `ReferenceTypeRA` in payload or apply partition.
- Apply: owner mismatch logs `[WARN]` and skips owner change (re-parent = delete+create policy) (1405-1421).
- `targets_rs`: resolve by GUID, warn/skip unresolved, replace sequence (1423+).

**T3:** Section (b) PASS -- `owner_guid` stable, `targets_rs` count 2, `ReferenceTypeRA absent` True, idempotent Apply PASS.

**Verdict:** **CONFORM**

---

## R4 -- IText media_uris

**Code:** `flexicon/code/Lexicon/TextOperations.py`

- Key `media_uris` with `{"uri", "file_guid"}` dicts; `cast_to_concrete` -> `MediaFilesOA` -> `MediaURIsOC` (406-428).
- `MediaFilesRC` removed from sync surface.
- Apply: absent/empty key leaves container; populated reconciles by URI add-only (484-536).
- Docstring documents `MediaFilesOC` vs `MediaURIsOC` open item; uses `MediaURIsOC` per T0.

**T3:** `(c) media_uris (R4)` **FAIL: unverified** -- no project with populated `MediaFilesOA`.

**Verdict:** **CONFORM** (implementation vs ruling 4.1-4.4). Live read/write of real media remains **unverified** (needs_human); does not contradict code-shape conformance.

---

## R5 -- ConstChartMovedTextMarker Create

**Code:** `flexicon/code/Discourse/ConstChartMovedTextOperations.py`

- Factory create -> `row.CellsOS.Add` -> `WordGroupRA` / `ColumnRA` -> `Preposed` (129-146).
- `# VERIFY in T3` comment present (choice (a) artifact); navigation via `WordGroupRA`, not phantom `MovedTextMarkerOA`.

**T3:** Section (d) full PASS -- Create no NRE, CellsOS membership, Preposed round-trip, Delete.

**Verdict:** **CONFORM** (binding ownership/order satisfied; T3 closed the Preposed gap beyond choice (a) minimum).

---

## R6 -- GetLanguages / SetLanguages

**Code:** `EtymologyOperations.py` 1214-1354

- `GetLanguages` / `SetLanguages` on `LanguageRS` with hasattr + transaction on set.
- `GetLanguage` / `SetLanguage` emit `[WARN]` and delegate to list API.

**T3:** `(a) GetLanguage/SetLanguage warn` PASS.

**T6 test fix:** `tests/operations/test_lexicon_brackets_live.py::test_setlanguage_persists_to_the_lcm` -- removed xfail/`LanguageRA` assertion; uses `SetLanguages` + fresh HVO re-read, or `SetLanguage(None)` clearing sequence when Languages list empty.

**Verdict:** **CONFORM**

---

## R7 -- ILexSense DoNotShowMainEntryInRC

**Code:** `flexicon/code/Lexicon/LexSenseOperations.py`

- `GetSyncableProperties`: only `DoNotPublishInRC` RC field; no `DoNotShowMainEntryInRC` key (662-670).
- `ApplySyncableProperties`: `_special_fields = ("SenseTypeRA", "DoNotPublishInRC")`; loop only `DoNotPublishInRC` (707-751).
- Docstring notes R7 absence (691-693).

**LexEntryOperations:** `DoNotShowMainEntryInRC` **still present** on entry sync/duplicate -- **in scope exclusion per T1b/T6 brief**, not an R7 violation.

**T3:** Section (e) PASS.

**Verdict:** **CONFORM**

---

## R8 -- IText.Name in sync payload

**Code:** `TextOperations.py` 383-387 (Get), Apply passes `Name` through base MultiString loop (449-481).

**T3:** `(c) Name in payload (R8)` PASS; keys `['en']`.

**Verdict:** **CONFORM**

---

## Non-ruling T6 action

| Item | Status |
|------|--------|
| Rewrite `test_setlanguage_persists_to_the_lcm` | Done (LanguageRS / SetLanguages) |
| Commit | Not performed (per binding) |

---

## References

- Rulings: `specs/325-syncable-properties/rulings.md`
- Live T3: `specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`
- Breaking scope R7 entry vs sense: `specs/325-syncable-properties/evidence/T1b-breaking-changes.md` section 3
