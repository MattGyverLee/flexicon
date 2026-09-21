# Resolution -- issue #352 (CopyAlternatives / multistring audit)

**Date:** 2026-09-21
**Branch:** `main` (uncommitted working tree)
**Method:** every type claim checked against `tests/contract/snapshots/liblcm_baseline.json`
**and** a live `hasattr`/type probe; every fix verified by a live round-trip
(`run_mode: live`). Evidence: `specs/352-copyalternatives-audit/evidence/live-*.md`.

## Fixed (all live-verified, regression tests in `tests/operations/test_352_*_live.py`)

| Batch | Sites | Fix | Evidence |
|---|---|---|---|
| SemDom (prior commit `a9463d3`) | `Duplicate`, `OcmCodes`, sync | scalar assign + `QuestionsOS` deep-copy | `live-proof.md`, `live-write.md` |
| DataNotebook | 15 Title/Text sites | bare-ITsString adapters; content = `DescriptionOA` paragraphs (new helpers) | `live-datanotebook.md` |
| Person | Gender/Email/Phone/notes/Duplicate/sync | int contract; field-less methods raise `FP_ParameterError`; notes retired (no `NotesOA` on `ICmPossibility`-based persons) | `live-person.md` |
| Note + annotation wrapper | `Source` x4 | `SourceRA` agent reference; find-or-create `SetAuthor` | `live-note.md` |
| Media + LexEntry etym | files + `:471` | audit row was wrong (objects are **ICmFile**); `Source`->`LanguageNotes` | `live-media-etym.md` |
| AnnoDef | HelpString/Prompt x8 | inherited `Description` | `live-annodef.md` |
| Discourse | cell Label/Comment x2 | shape dispatch (multi vs bare-ITsString) | `live-discourse.md` |
| Allomorph | StemName + AffixType sibling | `StemNameRA` / `MorphTypeRA` | `live-allomorph.md` |
| Text/Filter/Settings | Title/Description, title_pattern, `lp.Name` | dead Title branches removed; match `Name`; read-only `ShortName` | (in `test_352_text_filter_settings_live.py`) |
| ScrDraft | Description x4 + factory + accessor | scalar assign; `Create(description)`; wired `project.ScrDrafts` | `live-scrdraft.md` |
| ScrBook (sweep-doc follow-up) | Title x4 + accessor | `Title`->`Name`; wired `project.ScrBooks` | `live-scrbook.md` |

28 live tests pass (`-m requires_live_project`, live run_mode).

## Audit corrections (issue rows that were wrong)

- Media `Description`/`Copyright`: correct on ICmFile; no change needed.
- LexEntry/Pronunciation media `Copyright` guard: passes for files; correct.
- Text `Description`: present live (inherited; snapshot is declared-only) -- kept.
- `ILexEtymology.Source` counter-example in the old sweep doc: live `hasattr`
  is False; snapshot was right.
- Lesson (also noted in the sweep doc): snapshot absence is not absence.

## Adjacent bugs found live (fixed, same evidence files)

- DataNotebook `GetAll` (yielded the notebook), `Duplicate`/`GetParentRecord`
  owner dispatch, sync `__ResolveObject` typo (pinned-test updates in
  `test_datanotebook_duplicate.py`).
- Media `Duplicate` label order, `CompareTo`/`Delete` nonexistent members.
- `docstring_example_baseline.json` regenerated (26 stale ScrBooks/ScrDrafts
  entries removed; ratchet green).
- Sweep doc superseded with outcome table
  (`specs/agent-version-hotfix/reviews/unicode-vs-multiunicode-sweep.md`).

## Adjacent follow-ups (resolved 2026-09-21, evidence `live-adjacent.md`)

- 8 sibling `self.project._CompareValues` `CompareTo` call sites
  (Wordform, WfiMorphBundle, WfiGloss, Paragraph, Segment, Text,
  Discourse, WfiAnalysis): inline comparison + live self-compare tests.
- Stale `CmAnnotationType` docstring imports (16 sites): plain-int
  examples + notes; ratchet green.

## Open / follow-up (environmental)

- Set-valued allomorph `stem_name` round-trip needs `IMoStemName` rows
  (Sena 3; unavailable here -- no `.fwbackup`, installed copy will not open).
- `ScrDraft.Create` `type` label param accepted-but-unapplied.
- 4 PhaseE tests error without the Sena 3 backup (environmental, pre-existing).
