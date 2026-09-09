# Issue #276 -- GramCat walks the wrong collection

Status: PLANNED (unblocked -- data-model ruling obtained)
Issue: https://github.com/MattGyverLee/flexicon/issues/276
Related: #270 (found in passing), #163 (the OC/OS Duplicate fix on the
now-doomed TypesOC branch)

## 1. The defect

`GramCatOperations.GetAll` walks `lp.MsFeatureSystemOA.TypesOC`, whose
elements are `IFsFeatStrucType` -- not an `ICmPossibility`, no
`SubPossibilitiesOS`. So `recursive=True` silently truncates,
`Create(parent=)` and `GetSubcategories` cannot work, and `Delete`
removes from the wrong collection. Full site table in
`evidence/code-survey.md`.

This was never a casting bug. #270's cast sweep correctly refused to
paper over it.

## 2. The ruling (was the blocker)

Recorded in full in `evidence/domain-ruling.md`. In short:

- **"Grammatical category" at list level = Part of Speech**,
  `IPartOfSpeech` in `lp.PartsOfSpeechOA.PossibilitiesOS`.
- **At entry/sense level, "Grammatical Info." = the MSA**,
  `ILexSense.MorphoSyntaxAnalysisRA`, which references a POS and owns an
  `IFsFeatStruc`. Not a kind of category -- a different LCM class.
- **`IFsFeatStrucType` is never a grammatical category.** It is a
  structural template for feature structures. Wrong collection, full
  stop.
- Therefore `project.GramCat` becomes a **discoverability alias onto
  `POSOperations`**, per the `Features -> InflectionFeatures` precedent
  at `FLExProject.py:1681`. "Alias" here means *addresses the same
  list*, not *is the same object*: see the RESOLVED subsection at the
  end of section 4. `project.GramCat is project.POS` is **False**.

## 3. Why this is an alias and not a repoint

Repointing `GramCatOperations.GetAll` at `PartsOfSpeechOA` would leave
two independent CRUD surfaces over one list, with two `Create`
signatures, two `Duplicate` implementations, and two hierarchy walkers
to keep in sync. `POSOperations` already owns that list completely
(GOLD catalog, inflection classes, affix slots, entry counts). Both
legitimate readings of the name are already served; GramCat serves
neither. So the fix is subtraction plus one backfill, not a rewrite.

## 4. The one design sub-decision, and its resolution

Delegation is **not purely subtractive**. Verified against the code
(and correcting an assumption in the ruling):

| GramCat has | POSOperations has | Resolution |
|-------------|-------------------|------------|
| `GetAll(recursive=)` | `GetAll(recursive=)` | delegate, identical semantics |
| `GetSubcategories(recursive=)` | `GetSubcategories(recursive=)` | delegate, identical semantics |
| `GetParent(cat)` | **absent** | **backfill onto `POSOperations`** (T2) |
| `Create(name, parent=None)` | `Create(name, abbreviation, catalogSourceId=None)` | **hard break** (see below) |
| -- | `AddSubcategory(pos, name, abbreviation)` | covers the `parent=` use case |
| `Delete`, `GetName`, `SetName`, `Duplicate`, `GetSyncableProperties`, `ApplySyncableProperties`, `CompareTo` | all present | delegate |

### `GetParent` -- backfill, don't drop

`IPartOfSpeech` is a real possibility, so `GetParent` is a meaningful
operation on the POS list that `POSOperations` simply lacks. Add it
there. This is the "unify operations across types" rule in `CLAUDE.md`,
not new scope: the capability already exists in the codebase and only
needs to live at the right address.

### `Create` -- accept the break

`GramCat.Create("Transitive")` works today and `POS.Create` requires a
positional `abbreviation`, so a pure alias breaks it. Accept the break
rather than making `abbreviation` optional on `POS.Create`:

**There is no correct existing behaviour to preserve.** Every
`GramCat.Create` call ever made produced a stray `IFsFeatStrucType` in
the feature system (see ruling Q4). Breaking it breaks nothing that
worked. Softening `POS.Create` to accommodate it would degrade a
correct contract -- FLEx genuinely wants a POS abbreviation, it is what
interlinear renders -- in order to keep faith with a call that never
did what it claimed.

`GramCat.Create` therefore raises `FP_ParameterError` naming
`project.POS.Create(name, abbreviation)` and
`project.POS.AddSubcategory(parent, name, abbreviation)`.

### Keeping the name importable

`flexicon/__init__.py:147` exports `GramCatOperations` and
`tests/test_operations_baseline.py:79` imports it by name. Retain the
class as a **deprecated subclass of `POSOperations`** emitting
`DeprecationWarning`, matching the forwarding-with-warning pattern
already in `_op_aliases.make_op_namespace_alias`. Do not delete the
symbol in this change; schedule removal for the v5.0.0 boundary
alongside the `flexlibs2` shim.

### RESOLVED 2026-09-09 -- `project.GramCat` returns a distinct cached `GramCatOperations`, not `self.POS`

This section previously left an internal contradiction with sections 2
and 3, which can be read as requiring literal object identity
(`project.GramCat is project.POS`). **That reading is rejected, on live
evidence.** The literal `is`-identity is dropped; the raising `Create`
override above stands.

**The evidence.** An earlier task (T3) implemented the property as
`return self.POS`. Live verification showed that this defeats the
override entirely: `project.GramCat.Create("Transitive")` reaches
`POSOperations.Create` and raises a bare

    TypeError: POSOperations.Create() missing 1 required positional
    argument: 'abbreviation'

So the helpful `FP_ParameterError` -- with its pointer to
`project.POS.Create(name, abbreviation)` and
`project.POS.AddSubcategory(parent, name, abbreviation)` -- was
unreachable on the *exact* path real FlexTools / FlexTrans callers take.
The whole justification for keeping a removed method with its old
signature (see `Create -- accept the break`) is that it acts as the
migration signpost; an alias to `self.POS` deletes the signpost while
keeping the break.

**The resolution.** `FLExProject.GramCat` returns a lazily-cached
`GramCatOperations` instance, following the same
`if "_gramcat_ops" not in self.__dict__` convention as every sibling
`_*_ops` property (`_pos_ops` et al.). Caching is load-bearing, not just
an optimisation: `GramCatOperations.__init__` emits a
`DeprecationWarning`, so the instance must be constructed at most once
per project rather than once per attribute access.

Consequences, stated plainly so nothing downstream assumes otherwise:

- `project.GramCat is project.POS` -> **False**.
- `project.GramCat is project.GramCat` -> **True** (the cache).
- `isinstance(project.GramCat, POSOperations)` -> **True** (subclass).
- Reads (`GetAll`, `Find`, `GetName`, `GetSubcategories`, `GetParent`,
  ...) are inherited unchanged and still address
  `LangProject.PartsOfSpeechOA`.
- `project.GramCat.Create(...)` raises `FP_ParameterError`, with or
  without `parent=`.

**Section 3's concern is NOT reintroduced.** Section 3 rejected a
*repoint* because it would leave two independent CRUD surfaces over one
list -- two `Create` signatures, two `Duplicate` implementations, two
hierarchy walkers to keep in sync. None of that returns here.
`GramCatOperations` remains a **subclass** of `POSOperations` with
exactly one inherited implementation of every operation plus one
deliberate raising override. There is no second walker, no second
`Duplicate`, and no second *working* `Create` -- the override is a
signpost that writes nothing and opens no transaction. The distinctness
is at the level of the wrapper object only, never at the level of the
data or the implementation.

## 5. What the docstrings must say

`project.GramCat`'s docstring carries the disambiguation the name needs,
in the shape the `Features` alias already uses:

- `project.GramCat` / `project.POS` -- the **category inventory** (FLEx
  Grammar > Categories). Create, browse, nest, delete categories.
- `project.Senses.GetGrammaticalInfo(sense)` -- the sense's **MSA**, what
  FLEx labels "Grammatical Info." Use
  `project.Senses.GetPartOfSpeechObject(sense)` for just the category
  behind it, `project.MSA.*` to build one.
- `project.InflectionFeatures` -- the feature side of that composite,
  including `TypesOC` via `TypeFind`/`TypeCreate`.

## 6. Scope boundaries

**In scope:** the three-way ownership correction above, the broken
`.pyi`, the three false docstrings, the pinning test, the obsolete
mock-only Duplicate test, contract snapshot, migration notes, live
verification.

**Out of scope, filed as follow-ups (T13):**
- Cleanup guidance for stray `IFsFeatStrucType`s already written by
  `GramCat.Create`. Ruling Q4: document, never auto-migrate -- strays
  are indistinguishable from legitimate `TypeCreate` output and one may
  since be referenced via `TypeRA`. `needs_human`, not a script.
- Whether `POSOperations` exposes `IPartOfSpeech.DefaultFeaturesOA` /
  `InherFeatValOA` (ruling Q5). Real gap, unrelated to #276.

## 7. Risks

- **External callers.** FlexTools / FlexTrans scripts on disk may call
  `project.GramCat.*`. `GetAll`/`GetName`/`GetSubcategories` start
  returning POS data instead of feature types -- which is the point, but
  it is a semantic change to a public class. Needs a prominent
  MIGRATION_GUIDE entry, not just a CHANGELOG line.
- **The pinning test fails by design.** `TestGramCatGetAllRecursionClaim`
  asserts `"MsFeatureSystemOA" in` GetAll's source precisely so that
  nobody repoints GetAll without resolving this question. It has now
  been resolved, so the test must be updated in the same commit -- and
  its LCM-baseline half (`IFsFeatStrucType` is not a possibility) is
  still true and still worth keeping.
- **Live verification is mandatory.** This touches Create/Delete and a
  factory call, so `CLAUDE.md`'s live-LCM rule applies: Target project,
  `FLEXLIBS_REQUIRE_LIVE=1`, `run_mode: live` in
  `tests/live_status.json`, pre/post values re-read from the LCM. A
  mock-only pass is `FAIL: unverified`.
