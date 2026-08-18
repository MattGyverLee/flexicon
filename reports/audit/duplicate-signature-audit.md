# `Duplicate()` signature audit

Generated as a follow-up from the `test_duplicate_operations.py` live-verification
pass (2026-08-18). Purpose: catalogue every `Duplicate()` implementation under
`flexicon/code/`, compare its real (`.py`) signature against what its `.pyi` stub
claims, and flag disagreements. **No signatures were changed as part of this
audit** -- harmonising them is a breaking public-API change and is intentionally
out of scope here; this table is meant to seed a follow-up issue.

## Placement note

The task that produced this audit asked for it at `specs/duplicate-signature-audit.md`.
That could not be honored: the same task's instructions explicitly forbid touching
anything under `specs/` or `docs/` because of a concurrent 4.4.0 release cut in
those directories. Rather than silently comply with one instruction and violate
another, this file was placed at `reports/audit/duplicate-signature-audit.md`
instead (an existing, non-conflicting audit directory). Move it under `specs/`
once the release cut is clear of that directory, if that is still the desired
final location.

## Method

`grep -rn "def Duplicate" flexicon/code/` across both `.py` and `.pyi` files,
paired by class. "Real signature" is the actual `.py` `def Duplicate(...)` line.
"Stub claim" is the matching `.pyi` line. "Agree?" is whether a caller who
trusted the stub would get a `TypeError` in practice.

## Findings

**The stub generator emits one of two templates almost universally:**
`def Duplicate(self, obj: Any, deep: bool = True) -> Any: ...` or the fully
untyped `def Duplicate(self, *args: Any, **kwargs: Any) -> Any: ...`. Neither
reflects the real, per-class parameter lists below, which vary along three
independent axes:
- Presence/absence of `insert_after` (most classes have it; `LexEntryOperations`,
  `TextOperations`, `WfiAnalysisOperations`+`WfiGlossOperations`'s "no-op deep"
  siblings do not need it because their objects aren't ordered sequences)
- Presence/absence of `deep`
- Default value of `insert_after` when present -- **usually `True`, but
  `DataNotebookOperations` and `DiscourseOperations` default it to `False`**,
  an inconsistency worth calling out on its own.

## Table

| Class | File | Real `.py` signature | `.pyi` claim | Agree? |
|---|---|---|---|---|
| AgentOperations | Lists/AgentOperations.py:210 | `(self, agent_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No -- pyi invents `deep`, misses `insert_after` |
| AllomorphOperations | Lexicon/AllomorphOperations.py:371 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| AnnotationDefOperations | System/AnnotationDefOperations.py:1071 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No -- pyi misses `insert_after` |
| AnthropologyOperations | Notebook/AnthropologyOperations.py:1694 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| CheckOperations | System/CheckOperations.py:1345 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| ConfidenceOperations | Lists/ConfidenceOperations.pyi:19 | *(no `.py` override found -- inherits, likely from `possibility_item_base.py`)* | `(self, obj, deep=True)` | Unresolved -- audit did not trace inheritance chain |
| CustomFieldOperations | System/CustomFieldOperations.py:1401 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| DataNotebookOperations | Notebook/DataNotebookOperations.py:2452 | `(self, record_or_hvo, insert_after=False, deep=True)` | `(self, obj, deep=True)` | No -- also: `insert_after` default is `False` here, unlike most siblings |
| DiscourseOperations | TextsWords/DiscourseOperations.py:1060 | `(self, item_or_hvo, insert_after=False, deep=True)` | `(self, obj, deep=True)` | No -- same `insert_after=False` default outlier |
| EnvironmentOperations | Grammar/EnvironmentOperations.py:543 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| EtymologyOperations | Lexicon/EtymologyOperations.py:286 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| ExampleOperations | Lexicon/ExampleOperations.py:262 | `(self, item_or_hvo, insert_after=True, deep=False)` | `(self, obj, deep=True)` | No -- also `deep` default differs (`False` vs pyi's `True`) |
| FilterOperations | Shared/FilterOperations.py:1246 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| GramCatOperations | Grammar/GramCatOperations.py:446 | `(self, item_or_hvo, insert_after=True, deep=False)` | `(self, obj, deep=True)` | No -- default `deep` differs too |
| InflectionFeatureOperations | Grammar/InflectionFeatureOperations.pyi:21 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| LexEntryOperations | Lexicon/LexEntryOperations.py:296 | `(self, item_or_hvo, deep=True)` | `(self, *args, **kwargs)` | Loosely yes (untyped stub can't disagree, but also can't help IDEs/callers) |
| LexReferenceOperations | Lexicon/LexReferenceOperations.pyi:19 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| LexSenseOperations | Lexicon/LexSenseOperations.py:284 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, *args, **kwargs)` | Loosely yes (untyped) |
| LocationOperations | Notebook/LocationOperations.py:1161 | `(self, location_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| MediaOperations | Shared/MediaOperations.py:313 | `(self, item_or_hvo, deep=False)` | `(self, obj, deep=True)` | No -- default `deep` differs |
| MorphRuleOperations | Grammar/MorphRuleOperations.py:755 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| NaturalClassOperations | Grammar/NaturalClassOperations.py:353 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No -- pyi invents `deep` that doesn't exist |
| NoteOperations | Notebook/NoteOperations.py:258 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No -- pyi misses `insert_after` (though this is the one class whose real params happen to be the superset test code originally assumed universally) |
| OverlayOperations | Lists/OverlayOperations.pyi:19 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| ParagraphOperations | TextsWords/ParagraphOperations.py:246 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| PersonOperations | Notebook/PersonOperations.py:983 | `(self, person_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| PhonemeOperations | Grammar/PhonemeOperations.py:280 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| PhonologicalRuleOperations | Grammar/PhonologicalRuleOperations.py:1306 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| POSOperations | Grammar/POSOperations.py:862 | `(self, item_or_hvo, insert_after=True, deep=False)` | `(self, *args, **kwargs)` | Loosely yes (untyped) |
| PossibilityListOperations | Lists/PossibilityListOperations.py:591 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| possibility_item_base (shared base) | Lists/possibility_item_base.py:228 | `(self, item_or_hvo, insert_after=True)` | *(no dedicated `.pyi`; consumed via subclass stubs)* | N/A |
| ProjectSettingsOperations | System/ProjectSettingsOperations.py:1125 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| PronunciationOperations | Lexicon/PronunciationOperations.py:262 | `(self, item_or_hvo, insert_after=True, deep=False)` | `(self, obj, deep=True)` | No |
| PublicationOperations | Lists/PublicationOperations.pyi:18 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| SegmentOperations | TextsWords/SegmentOperations.pyi:18 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| SemanticDomainOperations | Lexicon/SemanticDomainOperations.py:1041 | `(self, item_or_hvo, insert_after=True, deep=True)` | `(self, obj, deep=True)` | No |
| TextOperations | TextsWords/TextOperations.py:221 | `(self, item_or_hvo, deep=True)` | `(self, obj, deep=True)` | **Yes** -- the one class where the generic stub template happens to be correct |
| TranslationTypeOperations | Lists/TranslationTypeOperations.pyi:19 | *(no `.py` override found)* | `(self, obj, deep=True)` | Unresolved |
| VariantOperations | Lexicon/VariantOperations.py:488 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |
| WfiAnalysisOperations | TextsWords/WfiAnalysisOperations.py:461 | `(self, item_or_hvo, insert_after=False, deep=False)` | `(self, obj, deep=True)` | No -- both defaults differ |
| WfiGlossOperations | TextsWords/WfiGlossOperations.py:389 | `(self, item_or_hvo, insert_after=False)` | `(self, obj, deep=True)` | No -- pyi invents `deep` that doesn't exist |
| WfiMorphBundleOperations | TextsWords/WfiMorphBundleOperations.py:243 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No -- pyi invents `deep` that doesn't exist |
| WordformOperations | TextsWords/WordformOperations.py:741 | `(self, item_or_hvo, deep=False)` | `(self, obj, deep=True)` | No -- default `deep` differs |
| WritingSystemOperations | System/WritingSystemOperations.py:1000 | `(self, item_or_hvo, insert_after=True)` | `(self, obj, deep=True)` | No |

## Recommendation (not actioned here)

1. Regenerate all `.pyi` stubs for `Duplicate()` from the real `.py` signatures
   rather than a fixed template -- the generator is clearly not introspecting
   the actual parameter list.
2. Separately decide (as a deliberate, versioned API decision, likely a v3.0/
   next-major change per this project's breaking-change conventions) whether to
   harmonise the real signatures themselves to one canonical shape. Candidates:
   - `(self, item_or_hvo, insert_after=True, deep=True)` for sequence-owned
     objects, or
   - `(self, item_or_hvo, deep=True)` for entry/text-level objects with no
     natural "position."
3. Fix the `insert_after` default-value outliers (`DataNotebookOperations`,
   `DiscourseOperations` default to `False`; everyone else defaults to `True`)
   as their own smaller, lower-risk follow-up, independent of #2.
