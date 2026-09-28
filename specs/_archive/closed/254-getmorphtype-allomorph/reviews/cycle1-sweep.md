# Cycle 1 sweep — docstring/name-promised type vs actual `*RA`/`*OA` field type

**Scope:** 111 `.py` files under `flexicon/code/` (`build/` excluded).
**Method:** four mechanical passes — (a) name-vs-field, (b) Get/Set pair
divergence, (c) resolver-vs-assignment-target, (d) docstring-vs-field.
**Result:** exactly one NEW high-confidence sibling — the write-side twin of
the reported getter. **No further instances found.**

## Findings

| file:line | method | field actually touched | type promised | type actually read/written | confidence |
|---|---|---|---|---|---|
| `flexicon/code/TextsWords/WfiMorphBundleOperations.py:877` | `SetMorphType` | `bundle.MorphRA` (assignment) | `IMoMorphType` (docstring `morph_type_or_hvo:`; resolver `__GetMorphTypeObject` at :1290 documents `IMoMorphType`) | `IMoForm` — the field is the bundle's allomorph slot | high |
| `flexicon/code/TextsWords/WfiMorphBundleOperations.py:825` | `GetMorphType` | `bundle.MorphRA` (return) | `IMoMorphType or None` | `IMoForm` | high (the already-reported bug; listed for completeness) |
| `flexicon/code/TextsWords/WfiMorphBundleOperations.py:1113` / `:1166` | `GetInflectionClass` / `SetInflectionClass` | `bundle.InflClassRA` | `IMoInflClass` | adjacent shape, NOT a type mismatch: `InflClassRA` is `hasattr`-guarded everywhere else in the same file (`:326`, `:376`) and in `WfiAnalysisOperations.py:561`, `WordformOperations.py:878`, but unguarded here — suspected nonexistent field on `IWfiMorphBundle` | medium |
| `flexicon/code/TextsWords/WfiMorphBundleOperations.py:1015` | `GetInflType` | `bundle.InflTypeRA` | docstring says `ICmPossibility` | actual is `ILexEntryInflType`; ancestor-type promise, doc-precision only | low |

## Passes that came back clean

- **(b) Get/Set pair divergence** — 60 `Get*`/`Set*` methods touch an
  `*RA`/`*OA`. Only `LexSenseOperations.GetPartOfSpeech` vs
  `SetPartOfSpeech` diverge (`MorphoSyntaxAnalysisRA` read vs
  `ToPartOfSpeechRA` write), which CHANGELOG L400-413 documents as
  deliberate (#87/#232). No action.
- **(c) resolver-vs-target** — 14 raw hits; 13 are the owner-object
  resolver (`__GetSenseObject`, `__GetBundleObject`, …) and are correct by
  construction. Only `:877` above is real.
- **(d) docstring-vs-field** — remaining hits are correct
  (`StratumRA`→`IMoStratum`, `WordGroupRA`→`IConstChartWordGroup`,
  `CategoryRA`→`IPartOfSpeech`, `ChartRA`→`IDsConstChart`,
  possibility-list fields promising `ICmPossibility`).
- `EtymologyOperations.GetLanguage`/`SetLanguage` (`:1248`/`:1278`) touch a
  nonexistent `LanguageRA` — already documented and deliberately unfixed in
  `docs/API_ISSUES_CATEGORIZED.md` Category 8. Not a new finding.

## Conclusion

The `GetMorphType`/`SetMorphType` pair in `WfiMorphBundleOperations.py` is
the whole population of this shape. **Fix both together** — a getter-only
fix leaves the setter writing an `IMoMorphType` into an `IMoForm` slot.

The issue's own sweep hint (`AllomorphOperations.GetMorphType`,
`LexEntryOperations.GetMorphType`) resolves NEGATIVE: both are correct.

## Carried forward for cycle 2

The medium-confidence `InflClassRA` finding is a *different* shape
(unguarded access to a possibly-nonexistent field, Category 8's other half)
and is cheap to settle with one live reflection call while the LCM session
is already open. Recommend folding it into the next live probe rather than
opening a separate issue before it is confirmed.

---
**Swept by:** Explore agent (cycle 1)
