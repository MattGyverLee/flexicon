# pyflexicon 4.10.0

**Released 2026-09-25** | `pip install --upgrade pyflexicon`

A repair release. Roughly sixty fixes since 4.9.0, most of them one bug
class: an operation that accepted an HVO (`int`) resolved it with
`project.Object(hvo)`, got back a bare `ICmObject`, and then failed or
silently did nothing when it reached for a type-specific member. No
signature was removed, and no default a caller passes explicitly changed
meaning; the behaviour changes are listed under
[Upgrade notes](#upgrade-notes) and each is a failure becoming loud, not a
working call becoming broken.

---

## The headline: HVO callers get the same object as everyone else

Most `*Operations` methods accept either an LCM object or its HVO. Until
this release, the HVO path was quietly second-class across Lexicon,
Grammar, Texts & Words, Lists and Scripture: examples, senses,
pronunciations, allomorph entries, segments, phonemes and phoneme codes,
phonological rules and features, inflection features, natural classes,
lexical references, possibility lists and items, wordforms, glosses,
Scripture books, sections, paragraphs and notes.

Every one of those resolvers now routes through `cast_to_concrete()`, and
`cast_to_concrete()` now knows sixteen more LCM classes than it did. That
second half matters: the resolver fixes merged first, and on their own they
did nothing, because a `ClassName` missing from the interface cache makes
the cast a silent no-op. The offline suite could not see that. The live
suite could, and the release was held until it passed.

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=False)

entry = next(iter(project.LexEntry.GetAll()))
pron = entry.PronunciationsOS[0]

# 4.9.0: AttributeError: 'ICmObject' object has no attribute 'Form'
# 4.10.0: the pronunciation form
print(project.Pronunciations.GetForm(pron.Hvo))
```

`cast_to_concrete()` is public (exported at the package top level), so
scripts that call it directly also benefit: it now returns the concrete
interface for `CmPossibilityList`, `CmBaseAnnotation`, `FsClosedFeature`,
`FsFeatureSystem`, `LexExampleSentence`, `LexPronunciation`,
`LexReference`, `LexEtymology`, `PhCode`, `PhFeatureConstraint`,
`RnResearchNbk`, `ScrBook`, `ScrSection`, `ScrTxtPara`,
`ScrScriptureNote` and `Segment`.

---

## Moves and reorders no longer delete data

Several move and reorder operations removed an object from its owning
sequence before adding it back. On an LCM owning sequence, `Remove` (and
`Clear`) **deletes** the object; it does not detach it. They now re-parent
with a single ownership transfer (`MoveTo` / `Add`), so nothing is
destroyed in between:

- sequence reorders on senses, examples, pronunciations, etymologies and
  morph bundles (#470)
- possibility re-parenting in Notebook and Lists, including
  `PossibilityLists.MoveItem` on part-of-speech subclasses (#448, #472)
- lexicon media and picture moves (#471)
- Scripture and discourse moves (#473)

---

## Also fixed

- **`ScrDrafts.Create` failed on every call.** The LCM `ScrDraftType` enum
  has exactly two members, `SavedVersion` and `ImportedVersion`. Pass
  `"saved_version"` (the default) or the new `"imported_version"`.
- **`MakeFeatStruc` accepts plain feature and value names** (#265), which
  failed with `ImportError` against a real LCM before this release's
  verification. Names resolve case-insensitively in the analysis writing
  system; an ambiguous name raises `FP_ParameterError`.
- **Note replies** (`Notes.AddReply`, `GetReplies`, `Duplicate`) and
  `Notes.GetAll` failed with `ActivationException`.
- **`PossibilityLists.GetParentItem`** always returned `None`.
- **`LexEntry.Duplicate(deep=True)`** failed on entries with allomorphs.
- **`LexEntry` / `LexSense` `MergeObject()` deduplication** had never
  removed anything (#318); see the upgrade notes.
- **`FLExProject.Object()`** and four GUID parses leaked raw CLR exceptions
  (#262, #334); they raise `FP_ParameterError` now.

`CHANGELOG.md`, section `[4.10.0]`, has every entry.

---

## Added

- **`FLExProject.SyncForeignChanges()`** (#292): mid-session ingest of
  changes other clients committed, under `OpenProject(undoable=False)`.
- **`OpenProject(..., strict_transactions=True)`** (#210): opt-in fail-fast
  when no rollback API is reachable, instead of degraded writes.
- **`Allomorphs.RemoveOrphaned()`** (#231): removes stale and invalid
  alternates from `AlternateFormsOS`.
- **`PossibilityLists.CreateItemInListByName()`** (#341), and
  `ConstChartClauseMarkers.InsertDependentClause` / `RemoveDependentClause`
  (#230).

---

## Upgrade notes

Each of these is a failure that used to be silent becoming visible.

- **`MergeObject(auto_deduplicate=True)`**, the default, can now raise
  `FP_DeduplicationError` when duplicates were found but not all of them
  could be removed. Pass `auto_deduplicate=False` to opt out while
  migrating (#318).
- **`FLExProject.Object()` with a stale HVO or GUID** raises
  `FP_ParameterError` rather than `System.Collections.Generic.
  KeyNotFoundException`. Update any `except KeyNotFoundException:` (#262).
- **Phoneme feature sync** raises `FP_ParameterError` for an unresolvable
  feature GUID; pass `on_unresolved="skip"` for the old behaviour (#253).
- **`PhonologicalRule.metathesis_parts`**, `PhonologicalContext.segment` and
  `.natural_class` return real data instead of empty values (#326).
- **`LocationOperations.SetCoordinates` / `SetElevation`** raise
  `FP_ParameterError`: `CmLocation` has no such fields in the LCM (#453).
- **`CompoundRule.left_context` / `right_context` / `contexts`** are
  removed; they were always `None` (#327).

### Deprecated, removed in v5.0.0

- `ScrDrafts.Create` type labels `"consultant_check"` and
  `"back_translation"`. They have no LCM member; they still create a saved
  version, as in 4.9.0, and now warn.
- `PhonologicalRule.has_redup_parts`, `.redup_parts`,
  `.as_reduplication_rule()`, `RuleCollection.redup_rules()` (#326).

---

## Known issues

Both are present in 4.9.0 and earlier; neither is a regression.

- **`InflectionFeatures.InflectionClassCreate`** fails on every call: it
  adds the class to the production-restrictions list rather than to a part
  of speech. Create inflection classes on `IPartOfSpeech.InflectionClassesOC`
  directly until this is fixed.
- **`ScrNotes.Create`** fails on every call: it stores notes under
  `book.FootnotesOS` rather than `Scripture.BookAnnotationsOS`.

---

## Verification

| Gate | Result |
|---|---|
| Offline suite (`-m "not requires_live_project"`) | **2446 passed, 0 failed** |
| Live suite (`-m requires_live_project`, `FLEXLIBS_REQUIRE_LIVE=1`) against Target, Sena 3 and sandbox copies | **976 passed, 0 failed**, 32 skipped, 2 xfailed, 1 xpassed; `run_mode: live` |
| LCM contract, including live contract verification | **23 passed**, 100% compatibility |

The first live run of this release candidate failed 25 tests. Every one
was a real defect or a test that had never run live. Two gates remain
parked, each with its reason in the test: the `RemoveOrphaned`
duplicate-lexeme gate (#231) is skipped because its setup cannot be built
through the LCM API, and the `ScrNotes.Create` paragraph gate (#504) is a
strict xfail on the known issue above.

The one xpass was a stale #449 marker for a `MorphRules.Delete` bug that
#467 fixed; the marker was removed and the test re-run live as a plain
pass. The other xfail is a pre-existing `ExampleOperations` literal
translation writing-system issue, already marked before this release.
