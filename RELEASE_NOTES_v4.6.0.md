# pyflexicon 4.6.0

**Released 2026-09-08** | `pip install --upgrade pyflexicon`

Six behavioural breaking changes, four new sync capabilities, and one
newly public export. Every breaking change is a correctness repair to
behaviour that was silently wrong -- no signature was removed, and no
default a caller passes explicitly changed meaning.

> ### This release also delivers 4.5.0, 4.5.1 and 4.5.2
>
> Those three versions were written into `CHANGELOG.md` but never tagged,
> so the PyPI publish workflow never fired and none of them shipped.
> **4.4.1 was the last version actually on PyPI.** If you are upgrading
> from 4.4.1 you are picking up four releases at once. Their changelog
> entries are retained as the historical record.

---

## Upgrading: what may change under you

### 1. `OpenProject()` now defaults to a headless UI (#285)

`ui=None` now resolves to a bare `HeadlessLcmUI()` rather than the
WinForms `FwLcmUI`. In a process with no WinForms message pump,
`FwLcmUI.ConflictingSave()` resolved to LCM's `RevertToSavedState()`
branch -- a conflicting save could silently discard your work. That
hazard is now closed by default.

`HeadlessLcmUI` is exported at the package top level for the first time:

```python
from flexicon import HeadlessLcmUI
```

Pass `ui=FwLcmUI(...)` explicitly if you genuinely need the WinForms
dialogs and have a message pump to service them.

### 2. Whitespace in name and text fields is now preserved (#242, Q-242A)

Writers across `Paragraph`, `Segment`, `Text`, `Anthropology`,
`Discourse` and `Check` operations previously validated emptiness
against a `.strip()`ed copy and then persisted *that stripped copy*,
silently discarding whitespace that was part of your string. The strip
is now a throwaway used only for the emptiness check; your original
value is what reaches the LCM.

Correspondingly, the sibling comparison methods (`TextOperations.Exists`,
`AnthropologyOperations.Find`, `CheckOperations.FindCheckType`, and seven
further name-keyed lookups) now strip **both** sides of the comparison,
not just the search argument -- so lookups still match against names
stored with incidental padding.

**If you relied on the old behaviour to normalise input, strip it
yourself before calling.**

### 3. `CheckOperations` rejects empty names instead of swallowing them (Q-242B)

`CreateCheckType`, `FindCheckType` and `SetName` previously coerced a
non-`str` payload or a whitespace-only string such as `" "` to `""` and
persisted or matched it with **no exception at all** -- total loss of the
intended name. All three now raise.

### 4. `WfiMorphBundleOperations.GetMorphType` returns the right type (#254)

It returned `bundle.MorphRA` -- the linked *allomorph* (`IMoForm`) --
under a method name promising a type. It now returns
`bundle.MorphRA.MorphTypeRA`, an `IMoMorphType`, which is what the name
always claimed.

**Any code that treated the result as an allomorph must now read
`bundle.MorphRA` directly.**

### 5. `SaveChanges()` guards against committing mid-transaction (#243)

Calling `SaveChanges()` with a unit of work open reached `usm.Save()`
unguarded, raising liblcm's `InvalidOperationException: "Commit at wrong
place."` -- and under `undoable=False` that failure collapsed the
session-long task envelope as a side effect, discarding the entire
pending change set with nothing written to disk (measured: 0 of 25
records survived).

It now raises `FP_TransactionError` when `CurrentDepth > 0`, before any
data can be lost.

---

## Added

- **`MSAOperations.GetSyncableProperties` / `ApplySyncableProperties`**
  (#251). `MSAOperations` previously had *zero* sync methods, so every
  MSA synced across projects with a correct `ClassName` and part of
  speech but a permanently null feature structure. Covers
  `MoStemMsa.MsFeaturesOA`, `MoInflAffMsa.InflFeatsOA`, and
  `MoDerivAffMsa`'s two independent slots.

- **`POSOperations` feature-structure sync** (#252). Captures and applies
  `DefaultFeaturesOA` and `InherFeatValOA`, neither of which was ever
  synced. Also repairs an independent hole on the HVO entry path, where
  `__ResolveObject` returned a bare uncast `ICmObject` and silently
  dropped even the four pre-existing properties.

- **`AllomorphOperations` `MsEnvFeaturesOA` sync.** Closes the same gap
  for `MoAffixAllomorph`.

- **`cast_to_concrete` is now public** (#271):
  `from flexicon import cast_to_concrete`. The documented escape hatch
  for direct-LCM work and legitimately polymorphic collections such as
  `ComponentLexemesRS`. Being total -- an unrecognised `ClassName`
  returns the object unchanged -- it is strictly safer than the
  `ILexEntry(x)` workaround it replaces.

## Fixed

- `FLExInitialize()` no longer swallows a genuine `Sldr.Initialize()`
  failure (#249).
- `BaseOperations._apply_props_loop` now resolves case- and
  whitespace-variant property keys.
- `FLExProject.CloseProject()` no longer skips `usm.Save()` when its own
  envelope close fails.
- Collection elements are cast to their concrete LCM interfaces (#270),
  and `LexEntryOperations.__ResolveObject` casts correctly (#269).
- The complex-form write path is repaired throughout (#272).

## Build

- **Python 3.14 and pythonnet 3.1 are now supported.** `requires-python`
  widens to `>=3.8,<3.15` and pythonnet to `>=3.0.3,<3.2`. The old `<3.1`
  pin carried no recorded rationale -- it arrived with the
  `flexlibs2` -> `flexicon` rename as an undocumented upper bound.

---

## Verification

| Gate | Result |
|------|--------|
| Offline suite (`-m "not requires_live_project"`) | **1732 passed, 695 deselected, 0 failed** |
| `local-compat-check` on `main` | green |
| `python -m build` | sdist + wheel built clean |

Live-LCM evidence for the write-path changes in this release was recorded
per-task under `specs/<feature>/evidence/` as each change landed; see
`docs/RELEASING.md` section 3 for the standing policy.

The offline figure supersedes the 1291 / 483 baseline recorded at
`33c5f7b`; the increase is new test coverage landing alongside these
fixes.

---

## Full detail

`CHANGELOG.md`, section `[4.6.0]`. Every entry carries its root-cause
analysis, the measurement that justified it, and its issue number.
