# pyflexicon 4.7.0

**Released 2026-09-09** | `pip install --upgrade pyflexicon`

One new bridge API that lets a single module source run under both
FlexTools and the FlexToolsMCP runner, two behavioural breaking changes in
`GramCat`, and two silent-failure repairs. No signature was removed, and
no default a caller passes explicitly changed meaning.

---

## The headline: `FLExProject.FromOpenProject(donor)`

Attach the full flexicon facade to a cache the **host already opened**, so
one module works unchanged in both runners:

```python
from flexicon import FLExProject

def Main(project, report, modifyAllowed):
    fx = FLExProject.FromOpenProject(project)
    lex, variants = fx.LexEntry, fx.Variants
```

Under FlexTools the donor is a *flexlibs* `FLExProject` -- the shallow
stable wrapper -- and the call attaches a flexicon view to its live cache.
Under the MCP the donor is already a flexicon `FLExProject`, so the call
returns it unchanged: `FromOpenProject(x) is x`, with the donor's
`_undoable` mode and cached operations untouched. It opens nothing, closes
nothing, and never mutates the donor.

**Why this matters.** This makes `from flexicon import FLExProject`
load-bearing for the first time. The template's long-standing advice to
import from flexicon explicitly could not do what it claimed: importing a
*class* has no effect on the *instance* FlexTools constructed and passed
in, so the import bound a name nothing used and `project.LexEntry` still
resolved against flexlibs. Scripts touching only the ~40 functions the two
wrappers share appeared to work -- which is exactly what made the gap hard
to notice.

### Lifecycle calls refuse on an attached view

A view must not be able to destroy the host's project, discard the host's
work, or report a save it did not make:

| Call | On an attached view |
|---|---|
| `Transaction()` | Supported |
| `UndoableOperation()` | `FP_TransactionError` -- the host holds a session-long non-undoable envelope; use `Transaction()` |
| `SaveChanges()` | `FP_RuntimeError` -- the host owns the save; just return |
| `AbortSession()` | `FP_RuntimeError` -- the host owns the unit of work; let the error propagate |
| `CloseProject()` | Silent no-op: returns `None`, never raises |

`AbortSession()` was the sharpest of these. A view is unconditionally
`_undoable = False`, so before the guard the call took the
`undoable=False` branch and `Rollback(0)`-ed the *host's* session-long
envelope -- discarding unsaved edits the host made before your module ever
ran -- then installed a replacement envelope the host did not open, and
reported success.

Its message deliberately does **not** point at `Transaction()` the way the
`UndoableOperation()` refusal does. A view is always Phase 1, where
`Transaction()` has no rollback at all (#236), so offering it to a caller
who asked to *discard* work would be a wrong answer in the shape of a
helpful one. **There is no module-side discard on a view:** let the
exception leave `Main()` and report it, and leave the keep-or-discard
decision to the host and its user.

---

## Upgrading: what may change under you

### 1. `project.GramCat` now addresses Parts of Speech (#276) -- BREAKING

`GramCatOperations` walked `LangProject.MsFeatureSystemOA.TypesOC`, whose
elements are `IFsFeatStrucType` -- a structural template for feature
structures, never a grammatical category. At list level a grammatical
category *is* a Part of Speech, in `PartsOfSpeechOA`.

`GetAll` / `Find` / `GetName` / `SetName` / `GetSubcategories` / `Delete` /
`Duplicate` therefore return and address **POS data instead of feature
types**, and `GetAll(recursive=True)` now descends the category hierarchy
instead of silently truncating.

- Wanted the feature-structure types? Use
  `project.InflectionFeatures.TypeFind` / `TypeCreate`.
- Wanted a sense's "Grammatical Info."? Use
  `project.Senses.GetGrammaticalInfo`.
- Otherwise: use `project.POS`. `GramCatOperations` is now a deprecated
  subclass of `POSOperations` and emits a `DeprecationWarning` once per
  project, on first access. **Removal is scheduled for v5.0.0.**

`project.GramCat is project.POS` is `False` -- it addresses the same list
and inherits the same behaviour, but stays a distinct instance so its
`Create` override stays reachable.

See `docs/MIGRATION_GUIDE.md` for migration steps.

### 2. `GramCatOperations.Create()` now raises and writes nothing (#276) -- BREAKING

`project.GramCat.Create("x")` raises `FP_ParameterError`. There was no
correct behaviour to preserve: every call added a stray `IFsFeatStrucType`
to the feature system, which surfaces in FLEx under **Grammar > Features**.
The message names `project.POS.Create(name, abbreviation)`,
`project.POS.AddSubcategory(parent, name, abbreviation)` and
`project.InflectionFeatures.TypeCreate(name, abbreviation)`.

**Projects written to by the old `Create` have strays to hand-clean.** No
automatic cleanup is offered, because a stray is indistinguishable from
legitimate `TypeCreate` output and may since have been referenced via
`TypeRA`.

### 3. Two getters that always failed silently now work (#277)

Both read property names absent from their target LCM type, and neither
raised -- callers got empty results or a reorder that could never run:

- **`EnvironmentOperations` reordering.** `_GetSequence` read
  `parent.EnvironmentsOA.PossibilitiesOS`, but `IPhPhonData` owns
  `EnvironmentsOS` directly. Every reordering method (`Sort`, `MoveUp`,
  `MoveDown`, `MoveToIndex`) raised `AttributeError` for environments.
- **`OverlayOperations.GetPossItems`.** It guarded on
  `hasattr(overlay, "SubPossibilitiesOS")`, but `ICmOverlay`'s surface is
  exactly `Name`, `PossItemsRC`, `PossListRA` -- so the guard was always
  `False` and the method returned `[]` for **every** overlay, always. On
  Sena 3 the one pre-existing overlay went from `[]` to all 859 items.

If you worked around either by reaching past the wrapper, you can drop the
workaround.

### 4. `flexicon.APIHelpFile` points at a file that exists (#240)

It named `docs\flexiconAPI\flexicon.html`, which was never generated. It is
now `docs\flexiconAPI\index.html`, the Sphinx root, confirmed present in a
built wheel.

---

## Also in this release

- **`POSOperations.GetParent(pos_or_hvo)`** (#276) -- returns the owning
  `IPartOfSpeech` for a subcategory, or `None` for a top-level category.
  The inverse of `AddSubcategory`; backfilled so the hierarchy capability
  `GramCatOperations` advertised survives the delegation.
- **`UndoableOperation()`'s refusal message tells the truth on a view.**
  The old wording blamed an `undoable=False` argument nobody passed -- the
  module never opened the project; the host did.
- **A cascade-delete test no longer swallows its own assertion** (#291).
  `try / except Exception: pass` caught the `AssertionError` the test
  existed to raise, so it reported green with cascade delete broken. A
  pattern audit found and fixed one genuine sibling.
- **Internal metrics scans report real numbers again** (#240). Two scans
  pointed at the pre-rename `flexlibs2/code`; `Path.rglob()` on a missing
  directory yields nothing without raising, so both had silently reported
  zero for months.

---

## Known limitation: the API docs site is still stale

The Sphinx build crash is **fixed** -- a pythonnet-emitted `HeadlessLcmUI`
type reflected with a null parameter name, which escaped autodoc as an
unhandled CLR exception and killed the process at exit 127, with no
traceback and no warning. `publish-docs.yml` also now fails in seconds
instead of queueing for GitHub's 24-hour limit.

**But the site still does not publish.** The workflow targets a
`[self-hosted, windows, fieldworks]` runner pool with zero runners
registered, and FieldWorks is genuinely required to import the package.
That is an open infrastructure decision -- see `docs/RELEASING.md`
section 1. Treat the published API documentation as manually maintained
and currently stale.

---

## Verification

| Gate | Result |
|------|--------|
| Offline suite (`-m "not requires_live_project"`) | **1795 passed, 716 deselected, 0 failed** |
| `python -m build` | sdist + wheel built clean |

The offline figure supersedes the 1732 / 695 recorded at the 4.6.0 cut;
the increase is new coverage landing alongside these changes.

Live-LCM evidence for the write-path changes was recorded per-task as each
change landed -- see `specs/flexicon-project-bridge/evidence/` for the
attached-view guards, and `docs/RELEASING.md` section 3 for the standing
policy.

---

## Full detail

`CHANGELOG.md`, section `[4.7.0]`. Every entry carries its root-cause
analysis, the measurement that justified it, and its issue number.
