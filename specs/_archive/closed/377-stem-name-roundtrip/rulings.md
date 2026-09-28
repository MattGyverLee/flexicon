# Issue #377 (item 1) -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/377-stem-name-roundtrip from origin/main

## Triage (cron)

| Priority | Open bug without an open PR |
|----------|-----------------------------|
| P0 | none |
| P1 | none |
| P2 | none (#231 slice 2 already in open PR #439) |
| **Selected** | **P3 #377** item 1 -- set-valued `stem_name` / `StemNameRA` live round-trip |

## Context

Issue #352 fixed `Allomorph.stem_name` to read `StemNameRA.Name` instead of the
nonexistent `StemName` multistring. Target has zero `IMoStemName` catalog rows,
so a **set-valued** round-trip could not be live-proven there
(`specs/352-copyalternatives-audit/evidence/live-allomorph.md`). Sena 3 carries
real `StemNamesOC` data under part-of-speech objects.

## RULING (binding)

1. Add **live regression** on `sena3_sandbox` (writable temp copy -- no mutation
   of the user's Sena 3 project):
   - Resolve one catalog `IMoStemName` from any `IPartOfSpeech.StemNamesOC`.
   - Create a `TEST_377_*` stem allomorph, assign `StemNameRA` on the concrete
     `IMoStemAllomorph`, then **re-query by HVO** and assert
     `Allomorph(...).stem_name` matches `best_analysis_text` of the catalog name.
2. Add a **read-only** live check on an existing Sena 3 stem allomorph that
   already has `StemNameRA` set (when present), same assertion shape.
3. **Out of scope:** new public setters on `AllomorphOperations`, closing #377
   (items 2-3 landed elsewhere; item 1 alone remains), live verification on
   cloud hosts without FieldWorks.

## Verification plan

- Offline ratchet: `tests/operations/test_issue377_stem_name_roundtrip_offline.py`
- Live (required when LCM available):
  `tests/operations/test_issue377_stem_name_roundtrip_live.py` with
  `FLEXLIBS_REQUIRE_LIVE=1` and `sena3_sandbox`
- Evidence: `specs/377-stem-name-roundtrip/evidence/offline-377-stem-name.md`
