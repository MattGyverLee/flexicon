# Pattern audit evidence -- issue #325 (T4 unblock)

**Date:** 2026-09-22  
**Working directory:** `C:/Github/flexicon-325`  
**Scope:** `flexicon/code/**/*Operations.py`  
**Method:** Horizontal sweep per `sweep-pattern` skill -- regex extraction of
`GetSyncableProperties` bodies, `hasattr(..., *RA|*RC)` usage, sync payload
keys, and `Duplicate` copy blocks; cross-check against
`tests/contract/snapshots/liblcm_baseline.json` and campaign T0 JSON under
`specs/325-syncable-properties/evidence/live-T0-*.json`; aligned with
`tests/test_syncable_properties_member_ratchet.py` interface map (41 Operations
files with `GetSyncableProperties`).

**Triage policy:** Siblings are listed for T9 (lex-archivist) filing only.
No out-of-scope fixes in this task.

---

## Pattern audit: dead `hasattr` / wrong-suffix LCM member in sync and copy paths

**Bug class:** Code guards sync or copy with `hasattr(item, "XxxRA")` /
`hasattr(item, "XxxRC")` (or assigns a non-existent member in `Duplicate`)
where the name is absent from the LCM surface for the typed interface (or
never existed). The guard is always false (or the assignment is a no-op),
so the sync payload key is permanently empty or copy silently skips data --
same defect class as issue #325 / R7 (`DoNotShowMainEntryInRC` on
`ILexSense`).

**Original sites (fixed in #325 scope -- do not re-file):**

| Site | Ruling | Remediation (in branch) |
|------|--------|-------------------------|
| `Lexicon/EtymologyOperations.py` -- `LanguageRA`, `LanguageNotesRA` in GSP / Apply | R1, R2 | `language_rs` from `LanguageRS`; phantom keys removed |
| `Lexicon/EtymologyOperations.py` + `Lexicon/LexEntryOperations.py` -- `LanguageNotesRA` in `Duplicate` | R2 | Dead blocks removed |
| `Lexicon/LexReferenceOperations.py` -- `ReferenceTypeRA` in GSP | R3 | `owner_guid` + `targets_rs`; phantom key removed |
| `TextsWords/TextOperations.py` -- `MediaFilesRC` in GSP | R4 | `media_uris` via concrete `MediaFilesOA` -> `MediaURIsOC` |
| `TextsWords/TextOperations.py` -- missing `Name` in GSP | R8 | `Name` added to GSP / Apply |
| `Lexicon/LexSenseOperations.py` -- `DoNotShowMainEntryInRC` in GSP / Apply | R7 | Key and handlers removed |
| `Lexicon/EtymologyOperations.py` -- `GetLanguage` / `SetLanguage` via `LanguageRA` | R6 | Deprecated wrappers; `GetLanguages` / `SetLanguages` |

Live proof for the wave-1 write path:
`specs/325-syncable-properties/evidence/live-T3-syncable-properties.md`
(`run_mode`: live).

**Siblings found (out of scope -- file for T9):**

- `flexicon/code/Lexicon/VariantOperations.py:618` [HIGH] T2e ratchet:
  `hasattr(item, "ShowComplexFormsIn")` in `GetSyncableProperties`; baseline
  `ILexEntryRef` has `ShowComplexFormsInRS`, not `ShowComplexFormsIn` -- dead
  sync key (allowlisted in `tests/test_syncable_properties_member_ratchet.py`).
- `flexicon/code/Lexicon/VariantOperations.py:569` [HIGH] `Duplicate` copies
  `ShowComplexFormsIn` under the same phantom name; should use
  `ShowComplexFormsInRS` sequence semantics.
- `flexicon/code/TextsWords/TextOperations.py:1081` [HIGH] `GetMediaFiles` reads
  `MediaFilesOA.MediaFilesOC`; T0 confirmed container collection is
  `MediaURIsOC` (`live-T0-media-raw.json`) -- same wrong-suffix class as R4;
  GSP fixed but helper APIs still broken until follow-on.
- `flexicon/code/TextsWords/TextOperations.py:1150` [HIGH] `AddMediaFile` adds
  to `MediaFilesOC` -- same `MediaFilesOC` vs `MediaURIsOC` discrepancy.
- `flexicon/code/Notebook/AnthropologyOperations.py:2009` [HIGH]
  `hasattr(anthro_item, "AnthroCode")` in GSP; `AnthroCode` absent from
  `ICmAnthroItem` baseline (file header documents phantom; OCM lives on
  `Abbreviation`).
- `flexicon/code/Notebook/AnthropologyOperations.py:2014` [HIGH]
  `hasattr(anthro_item, "CategoryRA")` in GSP; `CategoryRA` absent from
  baseline -- dead key (maps sync field `"Category"`).
- `flexicon/code/Notebook/DataNotebookOperations.py:2722` [MED]
  `hasattr(record, "Type")` / `Status` / `Confidence` / `DateOfEvent` in GSP;
  `ICmDataNotebookRecord` is not in the liblcm baseline snapshot (no live
  instances in T0 project set) -- cannot confirm names without live reflection;
  shape matches #325 guard-on-wrong-name class.
- `flexicon/code/Notebook/PersonOperations.py:1109` [HIGH]
  `hasattr(person, "LanguagesRC")` in GSP; `LanguagesRC` absent from
  `ICmPerson` baseline (`PlaceOfBirthRA`, `PositionsRC`, `PlacesOfResidenceRC`
  are present) -- languages never sync.
- `flexicon/code/System/AnnotationDefOperations.py:1206` [HIGH] GSP
  `hasattr(anno_def, "AnnotationType")` -- not on `ICmAnnotationDefn` baseline.
- `flexicon/code/System/AnnotationDefOperations.py:1208` [HIGH] GSP
  `hasattr(anno_def, "InstanceOf")` -- baseline exposes `AllowsInstanceOf` /
  `InstanceOfSignature`, not `InstanceOf`.
- `flexicon/code/System/AnnotationDefOperations.py:1212` [HIGH] GSP
  `hasattr(anno_def, "AllowsMultiple")` -- baseline field is `Multi`, not
  `AllowsMultiple` (issue #352 family).
- `flexicon/code/Lists/ConfidenceOperations.py:171` [HIGH] Repository scan uses
  `hasattr(analysis, "ConfidenceRA")`; `ConfidenceRA` absent from
  `IWfiAnalysis` baseline -- queries always empty.
- `flexicon/code/Lists/ConfidenceOperations.py:233` [HIGH] Same pattern on
  `IWfiGloss` / `ConfidenceRA` in `GetGlossesWithConfidence`.
- `flexicon/code/Lists/OverlayOperations.py:173` [HIGH] `IsVisibleRA` guarded
  in `IsVisible` / `SetVisible`; `ICmOverlay` not in baseline; live reflection
  for #277/#320 documented surface is `PossItemsRC`, `PossListRA` only --
  visibility helpers are likely no-ops.
- `flexicon/code/Lists/OverlayOperations.py:482` [MED] `ChartRA` fast path in
  `GetChart`; same overlay surface note -- ownership walk is the working path.

**Explicit notes (requested triage, not additional T9 lines unless confirmed dead):**

- **ConstChartClauseMarkerOperations / WordGroupRA:** `Create` (line 132) and
  `GetWordGroup` (line 291) use `WordGroupRA`; live discourse T0 dir lists
  `WordGroupRA` on the moved-text / marker surface (`live-T0-discourse-raw.json`).
  Static baseline entry for `IConstChartClauseMarker` does not list
  `WordGroupRA`, but this is concrete-impl exposure, not a confirmed always-false
  guard on live objects -- **cleared** from sibling filing pending targeted
  live read on a chart with clause markers.
- **StratumRA:** `PhonologicalRuleOperations.py` / `MorphRuleOperations.py`
  `GetSyncableProperties` emit `StratumGuid` via `hasattr(rule, "StratumRA")`;
  `StratumRA` appears on multiple grammar rule types in the baseline snapshot.
  **Cleared** -- not the dead-key class. `MSAOperations.py` duplicate path
  logs `StratumRA` as intentional copy-gap warning only.
- **ExampleOperations.py** `hasattr(trans, "TypeRA")` inside
  `TranslationsOC` loop: `trans` is `ICmTranslation`; `TypeRA` is on baseline.
  **Cleared** -- ratchet false positive from mapping whole file to
  `ILexExampleSentence`.
- **TextOperations GSP** `hasattr(container, "MediaURIsOC")`: container is
  `ICmMediaContainer`, not `IText`. **Cleared** -- intentional nested access
  after R4 fix.

**Sites cleared / not enumerated:** 84 `hasattr(item, ...)` checks inside
mapped `GetSyncableProperties` implementations match the baseline interface
property list (automated sweep). Remaining Operations modules with GSP but no
`*RA`/wrong-suffix hits in this class were not line-enumerated (~26 files).
Full grammar/discourse `Duplicate` trees were not exhaustively listed where no
`*RA` phantom matched the #325 failure mode.

**Offline ratchet:** `tests/test_syncable_properties_member_ratchet.py` guards
future GSP drift; it is complementary to this audit, not a substitute.

**Sibling count (T9 filing):** **15** line items marked [HIGH] or [MED] above
(2 VariantOperations sites, 2 TextOperations media helper sites, 2 Anthropology
fields, 1 DataNotebook block, 1 Person, 3 AnnotationDef phantoms, 2 Confidence,
2 Overlay).
