# Cycle 1 — Sweep Audit (issue #224)

**Agent:** Explore
**Scope:** Every callsite of `BestAnalysisVernacularAlternative` / `BestAnalysisAlternative` /
`BestVernacularAlternative` in `flexicon/code/`, classified SAFE vs UNSAFE.

**Result: SAFE = 15, UNSAFE = 1.**

The single UNSAFE hit is the #224 bug itself: `FLExProject.py:3355`, where `mua` comes from
`DomainDataByFlid.get_MultiStringProp` (an ITsMultiString) and `.BestAnalysisVernacularAlternative`
is invoked on it. Every other real-code callsite reads the accessor off an LCM model property
(`.Name`/`.Abbreviation`/`.Form`/`.Title` obtained via OA/OS/RA/RC), which yields
IMultiAccessorBase and is safe.

| File:Line | Object expr | Inferred type | Verdict | Reason |
|---|---|---|---|---|
| code/FLExProject.py:3355 | `mua.BestAnalysisVernacularAlternative` | ITsMultiString | UNSAFE | `mua = DomainDataByFlid.get_MultiStringProp(...)` — ITsMultiString lacks this accessor (the #224 bug) |
| code/System/WritingSystemOperations.py:903 | `string_obj.BestAnalysisVernacularAlternative` | IMultiString/IMultiUnicode | SAFE | isinstance guard at 899-900 |
| code/Shared/string_utils.py:224 | `multi_obj.BestAnalysisVernacularAlternative` | (param) | SAFE | `best_text()` has no callers; nothing feeds it a get_MultiStringProp object |
| code/Shared/string_utils.py:179 | `multi_obj.BestAnalysisAlternative` | IMultiUnicode | SAFE | all `best_analysis_text` callers pass model `.Name`/`.Abbreviation` |
| code/Shared/string_utils.py:201 | `multi_obj.BestVernacularAlternative` | (param) | SAFE | `best_vernacular_text` has no callers |
| code/Lexicon/ExampleOperations.py:1549 | `pub.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | pub from `example.DoNotPublishInRC` (CmPossibility) |
| code/Lexicon/LexEntryOperations.py:377 | `morph_type.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | morph_type is IMoMorphType |
| code/Grammar/PhonologicalRuleOperations.py:1220 | `bm.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | bm from BoundaryMarkersOC |
| code/Grammar/PhonologicalRuleOperations.py:1223 | `bm.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | bm from BoundaryMarkersOC |
| code/Shared/FilterOperations.py:1141 | `pos.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | pos is IPartOfSpeech |
| code/Shared/FilterOperations.py:1154 | `mt.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | mt from LexemeFormOA.MorphTypeRA |
| code/Shared/FilterOperations.py:1166 | `entry.LexemeFormOA.Form.BestVernacularAlternative` | IMultiUnicode | SAFE | OA property Form |
| code/Shared/FilterOperations.py:1198 | `wordform.Form.BestVernacularAlternative` | IMultiUnicode | SAFE | IWfiWordform.Form |
| code/Shared/FilterOperations.py:1223 | `genre.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | genre from GenresRC |
| code/Shared/FilterOperations.py:1236 | `text.Title.BestAnalysisAlternative` | IMultiString | SAFE | IText.Title |
| code/Lexicon/morphosyntax_analysis.py:433 | `pos.Name.BestAnalysisAlternative` | IMultiUnicode | SAFE | pos = self.pos_main (IPartOfSpeech) |

**Excluded:** docstring/`Example::`/`>>>` occurrences (BaseOperations, FLExProject docstrings,
lcm_casting 58/314/384/385/713/714, morphosyntax 194, phonological_rule 171), `*.backup`, and
`LexEntryOperations.py:1076` (method `GetBestVernacularAlternative` uses `get_String`, not the accessor).
