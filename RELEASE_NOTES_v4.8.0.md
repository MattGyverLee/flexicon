# pyflexicon 4.8.0

**Released 2026-09-10** | `pip install --upgrade pyflexicon`

A correctness release. Its theme is **silent failure**: operations that
reported success while writing nothing, predicates that contradicted their
own documented contract, and writing-system alts that were discarded
without a word. Two behavioural breaking changes ship with it. No
signature was removed, and no default a caller passes explicitly changed
meaning.

---

## Read this first: two behavioural breaking changes

### 1. `WritingSystemOperations.Exists()` is now active-only

Its docstring said "active only" three times; the body walked the
unfiltered LDML store. So it returned `True` for a writing system that was
present in the store but not in `CurVernWss` / `CurAnalysisWss` -- a
deactivated or template-inherited one -- contradicting `GetAll()`, which
every other consumer treats as ground truth.

```python
# Old whole-store behaviour, under its own name:
project.WritingSystems.ExistsInStore("fr-FR")   # new in 4.8.0
```

### 2. The complex-form-type accessors now raise instead of no-opping

`LexiconSetComplexFormType()` gated its entire body on
`hasattr(entry_ref, "ComplexEntryTypesRS")` with no `else`. pythonnet
surfaces only the static type's attributes, so that check was `False` for
any `entry_ref` that arrived as a bare `ICmObject` -- from an HVO, or any
round-tripped path. **The setter did nothing and reported success**; the
getter returned `None` as though no type were set. Both now cast first and
raise `FP_ParameterError` when the object genuinely is not a
`LexEntryRef`.

---

## The largest change: ~44 resolvers that never cast (#275)

Generalises the `LexEntryOperations` fix from #269 to its siblings across
**24 Operations classes**. Each carried the same two defects:

- the non-int branch returned the object **uncast**, so an object arriving
  as `ICmObject` from a polymorphic LCM collection raised
  `AttributeError` on the very next attribute access; and
- the HVO branch guarded with `isinstance(obj, ISomething)` against
  `FLExProject.Object()`, which is *declared* to return `ICmObject` and so
  evaluated `False` even for genuine instances, raising a spurious
  `FP_ParameterError`.

This is a **strict widening**: it accepts everything the previous guards
accepted, plus the genuine objects they falsely rejected. Legitimate
rejections -- an `ILexSense` HVO passed where an `ILexEntry` is required
-- still raise. 17 sites are proven live; the rest are offline-verified by
identical shape to a live-proven sibling, and the evidence file states
that split per class rather than claiming uniform live coverage.

---

## The importable surface is now honest

13 fully-wired Operations classes were advertised by the API index but
could not actually be imported -- `from flexicon import MSAOperations`
raised `ImportError` while `project.MSAs` worked fine. All 13 are now
exported (#311, #257):

`ConstChartCellTagOperations`, `ConstChartClauseMarkerOperations`,
`ConstChartMarkerOperations`, `ConstChartMovedTextOperations`,
`ConstChartOperations`, `ConstChartRowOperations`,
`ConstChartWordGroupOperations`, `LocalizedListsOperations`,
`MSAOperations`, `PhonFeatureOperations`,
`ReversalIndexEntryOperations`, `ReversalIndexOperations`,
`StratumOperations`.

`flexicon/__init__.pyi` now also declares the full public surface (#297),
so a correctly-typed downstream project no longer gets a Pyright error on
every `from flexicon import XOperations`. Parity is pinned by a test.

---

## Reorder operations that crashed on first use

Every reorder entry point -- `Reorder`, `MoveUp`, `MoveDown`,
`MoveToIndex` -- raised `AttributeError` or `ValueError` on
`TextOperations`, `ParagraphOperations`, `SegmentOperations`,
`WfiMorphBundleOperations` and `DataNotebookOperations` (#299, #300).
Three reached one level too deep into the owning object; two named a
sequence that does not exist. `ConstChartRowOperations.Create()` and
`SetLabel()` likewise crashed, calling `set_String` on
`IConstChartRow.Label`, which is a bare `ITsString` rather than an
`IMultiString` (#290).

---

## Writing systems

- **`Ensure(language_tag, name, is_vernacular=True) -> (ws, created)`**
  (new) -- idempotent activate-or-create. Collapses the old two-call
  `Exists()`-then-`Create()` dance, which *could not be written
  correctly*, because the two methods disagreed on what "exists" meant.
- **`ExistsInStore(language_tag)`** (new) -- the whole-store predicate
  `Exists()` used to answer by accident.
- **`Create()` no longer refuses to activate a store-present-but-inactive
  writing system** (#250). Previously such a writing system was
  permanently unreachable through the public API: `Exists()` said "yes",
  so callers could not safely `Create()` it, and `Create()` refused to
  activate it.
- **Two silent alt-drops closed** (#266, #267): a case- or
  separator-divergent writing-system tag no longer discards the
  `BasicIPASymbol` alt, or an example's `ICmTranslation` alt. #267's loop
  was restructured to resolve every target handle *before* creating and
  attaching the `ICmTranslation`, so an ambiguous spelling raises before
  anything is written rather than orphaning a zero-alt translation.
  **New failure mode:** where two distinctly cased/separated spellings in
  the target project normalize to the same form but resolve to different
  handles, these now raise `FP_ParameterError` naming both, where they
  previously degraded silently.
- Every remaining *legitimate* drop -- a target writing system genuinely
  absent under both exact and normalized matching -- is now
  **unconditionally logged**, not gated behind a `strict=` kwarg whose
  `False` default would have preserved the silent behaviour.

---

## If you compare suite numbers across releases, read this

#264 removed a duplicated, unguarded `Sldr.Initialize()` in
`tests/conftest.py`. Whichever module initialized SLDR first decided
pass/fail for hundreds of tests: the loser's raw call threw
`System.InvalidOperationException: The SLDR has already been
initialized`, uncaught, cascading an ERROR into every dependent test. An
**~1270-result discrepancy** was observed between two runs of the
identical offline command on the identical commit.

Counts recorded before this cut are therefore not reliable baselines.
This cut measured **1883 passed / 777 deselected**.

---

## Full detail

See `CHANGELOG.md` for the complete per-item record, including the
per-class list of the 24 Operations classes touched by #275 and the
`LexEntryRef` cast-registry gap fixed alongside it.
