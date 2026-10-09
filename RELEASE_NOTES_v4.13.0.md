# pyflexicon 4.13.0

**Released 2026-10-09** | `pip install --upgrade pyflexicon`

Inflection classes and exception features stop sharing a list. Inflection
classes are now read from and created on the part of speech that owns them,
exception features get their own helpers, and the MSA exception-feature
wrappers work on affix MSAs. **One behavioural breaking change**:
`InflectionClassCreate` needs `pos=` or `parent=`.

---

## Breaking: `InflectionClassCreate` needs an owner (issue 631)

`InflectionClassGetAll/Create/Delete` used
`MorphologicalDataOA.ProdRestrictOA` as the inflection-class store. That list
holds **exception features** (LCM's `ProdRestrict`), so `Create` wrote
inflection classes into the wrong list and `GetAll` raised as soon as a real
exception feature existed. Inflection classes belong to
`IPartOfSpeech.InflectionClassesOC`, or to a parent class's `SubclassesOC`.

```python
# Before
ic = project.InflectionFeatures.InflectionClassCreate("First Declension")

# After
noun = project.POS.Find("Noun")
ic = project.InflectionFeatures.InflectionClassCreate("First Declension", pos=noun)
sub = project.InflectionFeatures.InflectionClassCreate("Irregular", parent=ic)
```

With neither argument, `InflectionClassCreate` raises `FP_ParameterError`.
If both are given, `parent` wins, and a warning is logged when that parent is
not owned by `pos`. `docs/MIGRATION_GUIDE.md` has the full section.

---

## Exception features

- **New helpers** on `project.InflectionFeatures`: `ExceptionFeatureGetAll()`,
  `ExceptionFeatureFind(name)`, and
  `ExceptionFeatureCreate(name, abbreviation=None)`.
- **`MSAOperations.GetExceptionFeatures` / `AddExceptionFeature` /
  `RemoveExceptionFeature`** now work on affix MSAs, through
  `FromProdRestrictRC` / `ToProdRestrictRC`, and take `side="from"|"to"`
  (issue 630). `GetExceptionFeatures` logs a warning and returns `[]` for an
  unclassified affix or for an inflectional affix with `side="to"`.
  `Add` and `Remove` still raise in those cases.
- **`ChangeAffixVariant`** copies "from" exception features between
  inflectional and derivational affixes, and warns only about what is
  actually lost.

`CHANGELOG.md`, section `[4.13.0]`, has every entry.

---

## Known issues

- **`ScrNotes.Create`** fails on every call: it stores notes under
  `book.FootnotesOS` rather than `Scripture.BookAnnotationsOS`. This was
  carried over from 4.10.0 and is not a regression.

The `InflectionClassCreate` known issue from 4.10.0-4.12.0 is fixed in this
release.

---

## Verification

| Gate | Result |
|---|---|
| Offline suite (`-m "not requires_live_project"`) | **3719 passed** |
| Live suite (`-m requires_live_project`, `FLEXLIBS_REQUIRE_LIVE=1`) | **1132 passed**, 40 skipped, 2 xfailed; `run_mode: live` |

Evidence: `specs/release-4.13.0/evidence/live-release-gate.md`.
