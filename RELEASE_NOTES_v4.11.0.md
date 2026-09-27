# pyflexicon 4.11.0

**Released 2026-09-27** | `pip install --upgrade pyflexicon`

New readers (affix slots, MSA feature structures, sense-level publication
exclusion), HVO-everywhere duplicates, and the discourse-chart path rebuilt
on the real LCM ownership model. Contains one **BREAKING (behavioural)**
change -- new lexicon items publish everywhere again -- see
[Upgrade notes](#upgrade-notes). No signature was removed, and no default a
caller passes explicitly changed meaning.

---

## The headline: charts work now, on the real ownership model

`Discourse.CreateChart` raised on every call since it was written -- first
`NameError` on a stale factory name, then `FP_ParameterError` on a
collection (`ContentsOA.ChartsOC`) that does not exist in the LCM. Texts
carry no chart collection. Charts are owned project-level by
`lp.DiscourseDataOA.ChartsOC` and link to their text through the chart's
`BasedOnRA` reference to the text's StText contents -- every link of that
verified live by reflection before a line was rewritten:

```python
chart = project.Discourse.CreateChart(text, "Main Analysis")
assert project.Discourse.GetOwningText(chart.Hvo).Hvo == text.Hvo

# 4.10.0: NameError: name 'IConstChartFactory' is not defined
# 4.11.0: the chart, owned project-level, based on the text
```

`GetAllCharts` returns the text's charts instead of always yielding
nothing, `Duplicate` preserves the text link (and raises instead of
orphaning when the parent has no chart collection), and the cast registry
learned `DsDiscourseData`, which also un-breaks chart delete/duplicate
owner routing. One honest narrowing: `chart_type="discourse"` raises
`FP_ParameterError` -- the LCM exposes no discourse-chart factory, so
only constituent charts can be created through this API.

---

## HVO-everywhere duplicates

`Duplicate(insert_after=True)` looks the source up by HVO in eight more
operations, so a raw `project.Object(hvo)` source inserts after itself
instead of appending: Paragraph, WfiMorphBundle, NaturalClass, MorphRule,
PhonologicalRule, Environment, LexSense, Example (#531, #533, #535, #537,
#540, #548, #550, #552). Segments match by HVO the same way
(`Exists`, `MergeSegments`, `ReplaceAnalysis`; #523, #525, #528), and
`Paragraphs.GetOwningText` (#519) plus the MorphRule resolver (#561) take
HVO and raw views.

---

## Also fixed

- **New entries, senses, subsenses and examples are published in every
  publication again** (#545) -- the headline breaking change, see below.
- **Discourse chart/row pass-through resolvers cast before returning**
  (#510); chart/row delete and duplicate route through the typed owner
  (#513); paragraph `Duplicate` resolves its parent text (#517).
- **`POSOperations.AddSubcategory` accepts `catalogSourceId`** (#547),
  like `Create` already did.

`CHANGELOG.md`, section `[4.11.0]`, has every entry -- including the two
dozen merged since 4.10.0 that shipped without one until this cut.

---

## Added

- **Affix-slot readers and `AffixSlot` wrapper** (#542):
  `POSOperations.GetSlotName` / `SetSlotName` / `IsSlotOptional` /
  `SetSlotOptional` / `GetAffixesInSlot`; slot collections return
  wrappers with readable `.name`, `.optional`, `.affixes`.
- **`MSAOperations.GetInflAffMsaSlots`** (#543), the read-side pair for
  `SetInflAffMsaSlots`.
- **MSA feature-structure getters** (#544): `GetStemFeatures`,
  `GetInflAffFeatures`, `GetDerivFromFeatures`, `GetDerivToFeatures`,
  and dispatching `GetFeatures` -- the exact reverse of
  `InflectionFeatures.MakeFeatStruc`.
- **Sense-level publication exclusion** (#545): `GetDoNotPublishIn` /
  `AddDoNotPublishIn` / `RemoveDoNotPublishIn` on senses.
- **`AllomorphOperations.GetIsAbstract` / `SetIsAbstract`** (#546), and
  `Duplicate` copies the flag.
- **`InflectionFeatures.DescribeFeatStruc`** (#557): render a feature
  structure as readable text.
- **`LexSenseOperations.Create` over an entry-or-sense parent** (#567).

---

## Upgrade notes

- **New lexicon items publish everywhere again (#545).** 4.10.0 made
  every flexicon-created entry, sense, subsense, and example invisible
  in every publication until opted back in; there was not even a
  sense-level call to do it with. 4.11.0 restores the FLEx GUI default
  (visible until explicitly excluded) and adds the missing sense-level
  calls. Only scripts written against 4.10.0 that relied on born-excluded
  items are affected -- see the Migration Guide's new
  "Breaking Change: new lexicon items publish everywhere again" section.
- **Charts.** `CreateChart` succeeding where it always raised is the
  intended fix, but code that caught those exceptions will now take its
  success path; `GetAllCharts` returns charts where it returned none;
  `chart_type="discourse"` raises `FP_ParameterError` (it raised
  `NameError` before, so no working call changes).

---

## Known issues

Both carried over from 4.10.0; neither is a regression.

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
| Offline suite (`-m "not requires_live_project"`) | **2575 passed, 0 failed** |
| Live suite (`-m requires_live_project`, `FLEXLIBS_REQUIRE_LIVE=1`) against Target, Sena 3 and sandbox copies | **1040 passed, 0 failed**, 37 skipped, 2 xfailed, 5 subtests passed; `run_mode: live` |

The first live run of this release candidate failed 7 tests. Four were
real defects the offline suite cannot see (the chart factory name, the
chart ownership premise, the unregistered `DsDiscourseData` owner, and
`ReplaceAnalysis` dereferencing HVO-less elements); three were live
gates that had never run live (a `genre`-shaped `Texts.Create` call, an
iterator call on a collection, a blank-project entry assumption). All
seven are fixed with live read-back evidence under
`specs/release-4.11.0/evidence/live-release-gate.md`.
