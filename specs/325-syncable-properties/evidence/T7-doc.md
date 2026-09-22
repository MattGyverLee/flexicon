# T7 -- Documentation (lex-doc), issue #325

**Task:** T7
**Campaign:** 325-syncable-properties
**Date:** 2026-09-22
**Branch:** fix/325-syncable-properties (flexicon-325 worktree)
**Commit:** none (per binding)

## Inputs consumed

- `specs/325-syncable-properties/rulings.md` (R1-R8)
- `specs/325-syncable-properties/evidence/T1b-breaking-changes.md`
- `specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`

## Files touched

| File | Change |
|------|--------|
| `docs/API_ISSUES_CATEGORIZED.md` | Category 8: fixed stale `LanguageRS`/`GetLanguage` row; added five CORRECTED 2026-09-22 subsections (LanguageRS vs LanguageRA, ILexReference Owner/owner_guid, IText media_uris path, moved-text marker ownership, ILexSense DoNotShowMainEntryInRC vs entry scope) |
| `docs/MIGRATION_GUIDE.md` | Appended issue #325 sections: GetLanguage/SetLanguage deprecation + GetLanguages/SetLanguages; sync key renames/removals/additions; ConstChartMovedText Create model |
| `flexicon/code/Lexicon/EtymologyOperations.py` | Stale Create/Duplicate inline comments; expanded `GetSyncableProperties` docstring (language_rs, removed keys) |
| `flexicon/code/Lexicon/LexReferenceOperations.py` | Expanded `GetSyncableProperties` docstring (owner_guid, targets_rs) |

## Not changed (already current)

- `flexicon/code/TextsWords/TextOperations.py` -- GetSyncableProperties docstring already documents Name, media_uris, R4 note (T2c)
- `flexicon/code/Lexicon/LexSenseOperations.py` -- ApplySyncableProperties docstring already documents R7 absence of DoNotShowMainEntryInRC
- `flexicon/code/Discourse/ConstChartMovedTextOperations.py` -- Create docstring already documents row.CellsOS / setter order (R5)

## Evidence cross-reference

| Ruling topic | Category 8 subsection | Migration guide section | T3 evidence |
|--------------|----------------------|-------------------------|-------------|
| LanguageRS / language_rs | LanguageRS vs LanguageRA | Sync renames + GetLanguage deprecation | (a) PASS |
| LanguageNotes / Source | ILexEtymology Source table (unchanged) | LanguageNotesRA removal | (a) PASS |
| ILexReference owner_guid | ReferenceTypeRA vs Owner | Sync renames | (b) PASS |
| IText media_uris | MediaFilesRC vs MediaFilesOA | Sync renames (notes unverified) | (c) R4 FAIL unverified |
| Moved text marker | CellsOS ownership | ConstChartMovedText Create | (d) PASS |
| ILexSense RC field | DoNotShowMainEntryInRC | Sync removal | (e) PASS |

## Result

**PASS** -- documentation and migration entries aligned with T1 rulings and T1b migration bullets; docstring fixes limited to stale Etymology Create/Duplicate comments plus sync-key docstring expansion on Etymology and LexReference GetSyncableProperties.
