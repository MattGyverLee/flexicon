# Sweep: `Unicode` / `String` scalars mistaken for `MultiUnicode` / `MultiString`

**Origin:** v4.3.1 hotfix to `AgentOperations.GetVersion` / `SetVersion` (`ICmAgent.Version`).
**Date:** 2026-08-13
**Status:** UNVERIFIED — see "Reliability caveat" before acting on any row.

## The defect shape

Code treats a **monolingual `Unicode` / `String`** LCM property as if it were
**`MultiUnicode` / `MultiString`** — calling `.get_String(ws)` / `.set_String(ws, ...)`
or wrapping in `ITsString(...)` on a property pythonnet already surfaces as a plain
Python `str`. At runtime this raises `AttributeError: 'str' object has no attribute
'get_String'` on **every** call — or, where a broad `except AttributeError` wraps it,
silently returns a default.

The **inverse** shape also counts: assigning a plain `str` or a raw `ITsString`
directly to a property that genuinely is multilingual and needs `set_String()`.

### Reference exemplar (fixed in v4.3.1, excluded from counts)

`flexicon/code/Lists/AgentOperations.py` — `GetVersion` / `SetVersion`.
`ICmAgent.Version` is `Unicode` (plain `str`). Sibling `ICmAgent.Name` at line 261
*is* `MultiUnicode` and correctly uses `get_String` — the two live eight lines apart,
which is how the wrong pattern got copied.

## Reliability caveat — READ FIRST

This sweep was produced by a static-analysis pass that leaned partly on the
FlexToolsMCP casting index / `tests/contract/snapshots/liblcm_baseline.json`.
**That snapshot has confirmed coverage gaps.** Verified counter-example: it does not
list `ILexEtymology.Source`, a property `CLAUDE.md` documents as a real `IMultiString`
from the resolved issues #36/#39/#40. Compare FlexToolsMCP issue #86
("`get_object_api` omits inherited properties").

Consequences:

- The **call sites** below are real — the `get_String`/`set_String` calls exist at
  those lines, spot-verified by direct read for `PersonOperations.Gender`,
  `ScrDraftOperations.Description`, and `ConstChartRowOperations.Label`.
- The **type attributions** are inference, not ground truth. Every row needs a live
  `hasattr` / runtime check against a real FLEx project before a fix is written.
- The sweep's further claim that `docs/API_ISSUES_CATEGORIZED.md` Category 8 is
  "stale" re `Source` is **rejected** — it is an artifact of the same snapshot gap.
- The 26 "LIKELY / adjacent" hits rested most heavily on the snapshot and are the
  least trustworthy; they are recorded below but should be re-derived, not fixed.

## CONFIRMED shape (18) — needs live type verification

| file:line | receiver | inferred LCM type | why |
|---|---|---|---|
| `Scripture/ScrDraftOperations.py:171,270,310,349` | `draft.Description` | `Unicode` | `IScrDraft.Description` inferred scalar — same shape as `Version` |
| `Lexicon/SemanticDomainOperations.py:604,1262` | `domain.OcmCodes` | `Unicode` | OCM / Louw-Nida codes are single-value on `ICmSemanticDomain` |
| `Discourse/ConstChartRowOperations.py:132,298,337` | `row.Label` | `String` (ITsString) | single `String`; read `.Text`, write by assignment |
| `Discourse/ConstChartRowOperations.py:137,373,411` | `row.Notes` | `String` (ITsString) | same class, same basic signature |
| `TextsWords/DiscourseOperations.py:862,923` | `cell.Label` | `String` (ITsString) | `hasattr` guard passes, then `set_String` raises (862); 923 is swallowed by `except AttributeError` and silently returns `""` |
| `Lexicon/LexSenseOperations.py:3704` | `example.Reference` | `String` (ITsString) | `ILexExampleSentence.Reference` inferred single-string; also passes ws `0` |
| `Notebook/PersonOperations.py:445,486,1095` | `person.Gender` | `Integer` | `ICmPerson.Gender` inferred integer enum — not text at all |

## INVERSE (2)

| file:line | receiver | inferred LCM type | why |
|---|---|---|---|
| `System/ProjectSettingsOperations.py:165` | `self.project.lp.Name = ts` | `MultiUnicode` | assigns an `ITsString` straight to a multilingual accessor; needs `Name.set_String(ws, ts)` |
| `System/ProjectSettingsOperations.py:124` | `ITsString(self.project.lp.Name)` | `MultiUnicode` | read-side mirror. `Description` at 203/257 in the same file does it correctly — good in-file contrast |

## LIKELY / adjacent (26) — lowest confidence, re-derive before use

Receiver reported absent or non-string per the (gap-prone) snapshot:

- `Notebook/PersonOperations.py:602,647,1096` (`Email`), `:683,728,1100` (`PlaceOfBirth`, a reference atom)
- `System/AnnotationDefOperations.py:490,538,820,866,1201,1203` (`HelpString` / `Prompt`)
- `Notebook/DataNotebookOperations.py:317,629,685,1186,2571` (`Text`)
- `Scripture/ScrBookOperations.py:185,324,405,446` (`IScrBook` exposes `TitleOA`, an `IStText`, not `Title`)
- `Lexicon/SemanticDomainOperations.py:1253` (`Questions` → owning sequence `QuestionsOS`)
- `Shared/MediaOperations.py:253,947,1002` (`ICmMedia` has `Label`, not `Description`)
- `Lexicon/allomorph.py:279` (`StemName` → `StemNameRA`, an object)

Separately flagged: `Notebook/DataNotebookOperations.py:312,485,533,584,1181,2570` —
`IRnGenericRec.Title` exists but may be `String` rather than `MultiString`; verify the
`sig` in the LCM model before trusting `docs/FUNCTION_REFERENCE.md:1088`.

## Sanctioned path that these sites bypass

`BaseOperations._MakeTsString` / `_ReadTsString` (~lines 2240–2305) are the
single-string helpers and document exactly this Unicode-vs-Multi rule. Every
CONFIRMED site above bypasses them. Correct usage to copy:
`Lexicon/LexEntryOperations.py:1935,1977` and `Lexicon/LexSenseOperations.py:613,617`.
`Shared/string_utils.py` holds only multi-string helpers and has no type branch —
adding one there is a candidate follow-up.

## Recommended next step

Do **not** batch-fix from this table. Run a live verification pass over a real FLEx
project that, for each receiver, reports `type(obj.Prop)` and whether `get_String`
exists. Promote only the rows that come back monolingual, then fix those with the
`_MakeTsString` / `_ReadTsString` helpers and an AST regression test per site in the
style of `tests/test_agent_version_unicode.py`.
