# FlexLibs → Flexicon Migration Guide

Flexicon is a major version upgrade (2.0) with improvements to API consistency and user experience. This guide covers breaking changes and how to update your scripts.

> **[WARN] Newest breaking change:**
> [`project.GramCat` now addresses the Part of Speech list](#breaking-change-projectgramcat-now-addresses-the-part-of-speech-list).
> Any script calling `project.GramCat.*` is affected: `GetAll` / `GetName` /
> `GetSubcategories` now return categories instead of feature-structure types,
> and `GramCat.Create()` raises. Sections in this guide are appended in the
> order they were written; the newest is at the bottom.

## Breaking Change: Empty Multistring Field Handling

### What Changed

Flexicon **automatically converts FLEx's empty placeholder ("***") to Python's empty string ("")** in all functions that return multistring field values (glosses, definitions, forms, etc.).

| Behavior | FlexLibs (v1.x) | Flexicon (v2.0) |
|----------|-----------------|------------------|
| `LexiconGetSenseGloss(sense)` | Returns `"***"` | Returns `""` |
| `sense.Gloss.BestAnalysisAlternative.Text` | Returns `"***"` | Still returns `"***"` (raw C# result) |
| Requires `BestStr()` wrapping? | Sometimes | No (automatic) |

### Why This Changed

**Consistency Problem in FlexLibs:**
- Most methods use `or ""` fallback (don't explicitly handle "***")
- Some methods explicitly check for "***" (BestStr, custom fields)
- Users had to know which methods needed wrapping and which didn't

**Better UX in Flexicon:**
- All public functions automatically normalize empty strings
- Users write simpler, more Pythonic code
- No need to learn the "***" FLEx convention

### Migration: Check for "***"

If your script checks for the "***" placeholder, update it:

**Before (FlexLibs):**
```python
gloss = project.LexiconGetSenseGloss(sense)
if gloss == "***":
    print("Gloss is empty")
```

**After (Flexicon):**
```python
gloss = project.LexiconGetSenseGloss(sense)
if not gloss:  # or: if gloss == ""
    print("Gloss is empty")
```

### Migration: BestStr() Wrapping

If your script wrapped results with `BestStr()`, you can remove it:

**Before (FlexLibs):**
```python
# Sometimes needed because some methods return "***"
gloss = project.BestStr(sense.Gloss)
form = project.BestStr(entry.LexemeFormOA.Form)
definition = project.BestStr(sense.Definition)
```

**After (Flexicon):**
```python
# Not needed - these already return normalized strings
gloss = sense.Gloss.BestAnalysisAlternative.Text  # Still "***" if direct access
# Better: use the operation methods which do the normalization
# (This assumes we've created SenseOperations methods)
```

### Migration: Direct C# Field Access

If your script accesses C# objects directly (not through FlexLibs methods), you'll still get "***":

**Before (FlexLibs):**
```python
# Direct access - you see "***"
text = sense.Gloss.BestAnalysisAlternative.Text
if text == "***":
    print("Empty")
```

**After (Flexicon):**
```python
# Direct access still returns "***" (raw C#)
text = sense.Gloss.BestAnalysisAlternative.Text
if text == "***":
    print("Empty")  # Still need this check

# Better: use Flexicon operations methods
# (These do automatic conversion)
gloss = SenseOperations.GetGloss(sense)  # Returns ""
```

---

## Summary of Changes

| Feature | FlexLibs | Flexicon | Action |
|---------|----------|-----------|--------|
| Empty multistring handling | Inconsistent | Automatic (all functions) | Remove "***" checks, use `if not value:` instead |
| BestStr() utility | Available | Still available (but not needed) | Can remove from scripts |
| Direct C# field access | Returns "***" | Still returns "***" | If using direct access, keep "***" checks |
| Function return values | Mixed | Consistent "" | Update empty checks |

---

## Testing Your Migration

Quick checklist:
- [ ] Search your script for `== "***"` - change to `== ""` or `if not value:`
- [ ] Search for `BestStr()` calls - can usually remove them
- [ ] Test with entries/senses that have empty glosses/definitions
- [ ] Verify your conditional logic still works

---

## Questions?

See [CLAUDE.md](../CLAUDE.md) for more details on FLEx conventions and data handling.

---

## v2 to v3 Migration

Flexicon v3.0.0 (April 7, 2026) introduced two breaking changes. If you are upgrading from
any v2.x release, check both sections below.

### 1. Removed: `project.Reversal` API

The bundled `project.Reversal` namespace was removed entirely. Replace each call with the
equivalent modular API:

| v2.x (removed) | v3.0 replacement |
|---|---|
| `project.Reversal.GetAllIndexes()` | `project.ReversalIndexes.GetAll()` |
| `project.Reversal.GetAll(index)` | `project.ReversalEntries.GetAll(index)` |
| `project.Reversal.GetForm(entry)` | `project.ReversalEntries.GetForm(entry)` |
| `project.Reversal.SetForm(entry, text)` | `project.ReversalEntries.SetForm(entry, text)` |
| `project.Reversal.Create(index, form, ws)` | `project.ReversalEntries.Create(index, form, ws)` |
| `project.Reversal.AddSense(entry, sense)` | `project.ReversalEntries.AddSense(entry, sense)` |
| `project.ReversalIndex(ws)` | `project.ReversalIndexes.Find(ws)` |

**Before (v2.x):**
```python
for index in project.Reversal.GetAllIndexes():
    ws = index.WritingSystem
    for entry in project.Reversal.GetAll(index):
        print(project.Reversal.GetForm(entry))
```

**After (v3.0):**
```python
for index in project.ReversalIndexes.GetAll():
    ws = index.WritingSystem
    for entry in project.ReversalEntries.GetAll(index):
        print(project.ReversalEntries.GetForm(entry))
```

See [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md) for the complete 20-method table
and additional code examples.

### 2. Lists Consolidation (GROUP 8)

`AgentOperations`, `PublicationOperations`, `TranslationTypeOperations`, and `OverlayOperations`
now inherit from `PossibilityItemOperations`. For most callers **no code changes are needed** —
the same CRUD methods are available under the same names.

Known caveats:
- `AgentOperations` (#54) and `OverlayOperations` (#149) have partial parent-class fit problems;
  a small number of inherited methods may not function correctly in edge cases.

See [RELEASE_v3_0_0.md](internal/RELEASE_v3_0_0.md) for the full consolidation table and change details.

---

# v2.4 → v2.5 Migration

## Breaking Change: `flat=` → `recursive=` on hierarchical-list `GetAll`

### What Changed

Every hierarchical-list `GetAll()` accessor (POS, LexSense, SemanticDomain, Anthropology, Location, Publication, PossibilityLists, plus the inline `GetSubcategories` / `GetSubdomains` / `GetSubitems` helpers) standardized on a single parameter name. The old `flat=` is renamed to `recursive=` and the default is now `recursive=True` -- the intuitive "give me everything under this node" query is the one with no argument.

| Behavior | v2.4 | v2.5 |
|---|---|---|
| `POS.GetAll()` (no args) | Top-level only (~30) | All POSs including subcategories (~80) |
| `POS.GetAll(flat=True)` | Returns all | Raises `TypeError` |
| `POS.GetAll(recursive=False)` | -- | Top-level only |
| `LexEntry.GetAvailableMorphTypes(include_subcategories=True)` | Worked | Raises `TypeError` |
| `LexEntry.GetAvailableMorphTypes(recursive=True)` | -- | Works |
| `FLExProject.GetAllSemanticDomains(flat=True)` | Works | Raises `TypeError` |

### Why This Changed

The intuitive query ("give me everything under this category") was the harder one to spell when `flat=False` was the default for some accessors and `flat=True` for others. Standardizing on `recursive=True` as the default for collection queries lets the common case stay simple and the specialized case (`recursive=False`) stay explicit. See #100 and #101 for the full story.

### Migration: rename `flat=` to `recursive=`

**Before (v2.4):**
```python
poses = project.POS.GetAll(flat=True)
domains = project.SemanticDomains.GetAll(flat=True)
```

**After (v2.5):**
```python
poses = project.POS.GetAll()              # recursive by default
domains = project.SemanticDomains.GetAll()
# or, for top-level only:
top_poses = project.POS.GetAll(recursive=False)
```

### Migration: `include_subcategories=` -> `recursive=`

**Before:**
```python
mt = project.LexEntry.GetAvailableMorphTypes(include_subcategories=True)
```

**After:**
```python
mt = project.LexEntry.GetAvailableMorphTypes(recursive=True)
```

## Behavior Change: counting queries default to FLEx UI parity (direct-only)

### What Changed

Counting queries (`POSOperations.GetEntryCount`, `SemanticDomainOperations.GetSenseCount`) default to `recursive=False` -- they count only objects tagged with the requested category exactly, matching every count column FLEx itself surfaces (Categories tool, Lexicon Browse view, Tools > Statistics). The previous v2.4 default of `recursive=True` for `GetEntryCount` was reverted in #101 because users would see flexicon reporting ~3x the counts FLEx shows and assume flexicon was wrong.

The two distinct user questions:

- "How many entries match this tag?"             -> `GetEntryCount(noun)`            (direct, FLEx UI parity)
- "How many entries match this tag or descendants?" -> `GetEntryCount(noun, recursive=True)`

**No caller code change is required for the common path.** If you previously relied on the brief recursive=True default that shipped between d423e83 and the #101 revert, pass it explicitly.

### Migration

**Before (v2.4 / d423e83):**
```python
n = project.POS.GetEntryCount(noun)               # rolled up descendants
```

**After (v2.5):**
```python
n = project.POS.GetEntryCount(noun)               # direct-tagged only (FLEx UI parity)
n = project.POS.GetEntryCount(noun, recursive=True)  # roll up
n = project.SemanticDomains.GetSenseCount(dom)    # direct-tagged only
n = project.SemanticDomains.GetSenseCount(dom, recursive=True)  # roll up
```

### Migration: Detect-and-Fix Recipe

```bash
# Find all callers using the old flat= kwarg
rg --type py 'GetAll\(.*flat='
rg --type py 'GetAvailableMorphTypes\(.*include_subcategories='
```

Replace `flat=` with `recursive=` (same boolean value). Replace `include_subcategories=True` with `recursive=True`.

---

# v4.6 -> next Migration

## Breaking Change: `project.GramCat` now addresses the Part of Speech list

### What Changed

`GramCatOperations` walked `LangProject.MsFeatureSystemOA.TypesOC`, a
collection of `IFsFeatStrucType`. That was the wrong collection. An
`IFsFeatStrucType` is a structural template for feature structures -- it
declares which features may co-occur inside an `IFsFeatStruc` -- and it is
never a grammatical category.

At list level a grammatical category **is** a Part of Speech: `IPartOfSpeech`
in `LangProject.PartsOfSpeechOA`, the list `POSOperations` already owns
completely. So `GramCatOperations` is now a thin deprecated subclass of
`POSOperations`, and `project.GramCat` returns an instance of it that
addresses `PartsOfSpeechOA`.

`project.GramCat` is **not** `project.POS`. It is a distinct, lazily created
and then cached `GramCatOperations` instance -- `project.GramCat is
project.POS` evaluates to `False`. The distinction is deliberate: it is what
keeps `GramCat.Create()`'s explanatory override reachable on the path real
callers take (see below). `Create` is the only member that differs; everything
else is inherited unchanged, so both spellings address the same list and
return the same objects.

| Behavior | v4.6 and earlier | next release |
|---|---|---|
| `project.GramCat` | A separate `GramCatOperations` over `MsFeatureSystemOA.TypesOC` | A deprecated `GramCatOperations` -- a `POSOperations` subclass -- over `PartsOfSpeechOA`, created once and cached per project |
| `project.GramCat is project.POS` | `False` (different classes, different lists) | Still `False` -- a distinct instance addressing the same list, not the same object |
| `GramCat.GetAll()` | `IFsFeatStrucType` (feature-structure types) | `IPartOfSpeech` (categories) |
| `GramCat.GetAll(recursive=True)` | Silently truncated -- the elements are not possibilities and have no `SubPossibilitiesOS` | Descends the real category hierarchy |
| `GramCat.GetName(x)` / `SetName(x, n)` | Named a feature-structure type | Names a category |
| `GramCat.GetSubcategories(x)` | Could not work | Delegates to `POSOperations.GetSubcategories` |
| `GramCat.Create(name)` / `Create(name, parent)` | Wrote a stray `IFsFeatStrucType` into the feature system | Raises `FP_ParameterError` and writes nothing |
| `GramCat.Delete(x)` / `Duplicate(x)` | Addressed `TypesOC` | Address `PartsOfSpeechOA` |
| `GramCatOperations(project)` | Silent | Emits `DeprecationWarning` |
| First `project.GramCat` access | Silent | Emits `DeprecationWarning` -- the property constructs `GramCatOperations` on first access, so the warning fires once per project and later accesses reuse the cached instance silently |
| `GramCat.Find(...)` / `GramCat.Exists(...)` | Advertised by the type stub, `AttributeError` at runtime | Genuinely resolve, inherited from `POSOperations` |
| `POSOperations.GetParent(pos)` | Absent | Returns the owning `IPartOfSpeech`, or `None` for a top-level category |

`project.GramCat` is retained as a **deprecated discoverability spelling** so
that callers thinking in FLEx UI terms (Grammar > Categories) can still find
the wrapper. Removal is scheduled for the **v5.0.0** boundary. New code should
spell it `project.POS`.

### Why This Changed

Three FLEx concepts wear confusingly similar names. They are different LCM
classes, and only the first is a category (#276):

| You mean | FLEx calls it | LCM | Flexicon API |
|---|---|---|---|
| The inventory of categories | Grammar > Categories | `IPartOfSpeech` in `PartsOfSpeechOA` | `project.POS` (formerly `project.GramCat`) |
| A sense's "Grammatical Info." | Lexicon sense field | the MSA, `ILexSense.MorphoSyntaxAnalysisRA` | `project.Senses.GetGrammaticalInfo(sense)`, `project.MSA.*` |
| A feature-structure template | Grammar > Features (type list) | `IFsFeatStrucType` in `MsFeatureSystemOA.TypesOC` | `project.InflectionFeatures.TypeFind` / `TypeCreate` |

`GramCat` served the third while its name, its module placement and its own
docstrings promised the first. Because `IFsFeatStrucType` is not an
`ICmPossibility`, every hierarchy feature it advertised was unreachable. The
fix is subtraction plus one backfill (`POSOperations.GetParent`), not a second
CRUD surface over the category list.

### Migration: browsing, naming and deleting categories

No signature change -- but the objects you get back are different, so any code
that inspected them as feature-structure types needs revisiting.

**Before (v4.6):**
```python
for cat in project.GramCat.GetAll():          # IFsFeatStrucType
    print(project.GramCat.GetName(cat))
```

**After:**
```python
for pos in project.POS.GetAll():              # IPartOfSpeech
    print(project.POS.GetName(pos), project.POS.GetAbbreviation(pos))

# Hierarchy actually works now:
for sub in project.POS.GetSubcategories(pos, recursive=True):
    assert project.POS.GetParent(sub) is not None
```

### Migration: `GramCat.Create()` raises -- pick a replacement

`GramCat.Create(name, parent=None)` is retained with its old signature only so
that an existing caller gets an explanatory `FP_ParameterError` instead of a
bare `TypeError` about a missing `abbreviation`. It raises **before any
write**; nothing is created and no transaction is opened.

You get that error on the path a real caller takes -- through
`project.GramCat`, with the old two-argument-or-fewer call shape:

```python
>>> project.GramCat.Create("Transitive")
Traceback (most recent call last):
  ...
FP_ParameterError: GramCat.Create() has been removed (issue #276): it never
created a grammatical category. It created a stray IFsFeatStrucType in the
feature system (LangProject.MsFeatureSystemOA.TypesOC), which is a structural
template for feature structures, not a category. A list-level grammatical
category is a Part of Speech: use project.POS.Create(name, abbreviation) for
a top-level category, or project.POS.AddSubcategory(parent, name,
abbreviation) for a subcategory. If you did want a feature-structure type,
use project.InflectionFeatures.TypeCreate(name, abbreviation).
```

This is why `project.GramCat` is a distinct `GramCatOperations` instance
rather than `project.POS` itself. Had the property simply returned
`project.POS`, the call above would have reached `POSOperations.Create(name,
abbreviation)` and raised `TypeError: POSOperations.Create() missing 1
required positional argument: 'abbreviation'` -- which names neither the
replacement nor the reason -- and the explanatory error would only ever have
been reachable by constructing `GramCatOperations` by hand, which no existing
caller does.

There is no correct behaviour to preserve here: every `GramCat.Create` call
ever made added a stray `IFsFeatStrucType` to the feature system, not a
category. Creating a category genuinely requires an abbreviation -- it is what
interlinear renders -- so `POSOperations.Create` is not being softened to
accept the old call shape.

**Before (v4.6):**
```python
cat = project.GramCat.Create("Transitive")
sub = project.GramCat.Create("Transitive", parent=verb)
```

**After:**
```python
# Top-level category:
cat = project.POS.Create("Transitive", "tr")

# Subcategory:
sub = project.POS.AddSubcategory(verb, "Transitive Verb", "vt")

# If you actually wanted a feature-structure type:
ftype = project.InflectionFeatures.TypeCreate("Common agreement", "tCommonAgr")
```

### Migration: you actually wanted the feature-structure types

Everything the old implementation touched now lives on
`project.InflectionFeatures`:

| Old | New |
|---|---|
| `project.GramCat.GetAll()` | `project.InflectionFeatures.TypeFind(name)` for lookup by name |
| `project.GramCat.Create(name)` | `project.InflectionFeatures.TypeCreate(name, abbreviation)` |

### Migration: you actually wanted the sense's "Grammatical Info."

That field is the MSA, not a category:

```python
info = project.Senses.GetGrammaticalInfo(sense)       # the MSA composite
pos = project.Senses.GetPartOfSpeechObject(sense)     # just the category behind it
```

Use `project.MSA.*` to build one.

### [WARN] Clean-up: stray feature-structure types written by `GramCat.Create`

If your project was ever written to by `GramCat.Create`, it contains stray
`IFsFeatStrucType` entries carrying whatever name you passed -- they surface
in FLEx under **Grammar > Features** as unexplained entries in the type list
(for example "1st person" sitting alongside "tCommonAgr"). They are harmless
to analysis output, since nothing reads a type absent a `TypeRA` reference,
but they corrupt the Features inventory as presented to a linguist.

**Clean these up by hand in FLEx. No automatic cleanup is offered, and none
should be attempted.** A stray is indistinguishable from a type legitimately
created by `InflectionFeatures.TypeCreate`, and one may since have been wired
up via `TypeRA`. Deciding which is which requires a human looking at the
specific project -- delete only the entries you recognise as category names
that were never meant to be feature-structure types.

### Migration: Detect-and-Fix Recipe

```bash
# Every call through the deprecated spelling:
rg --type py 'project\.GramCat\.'

# The calls that now raise:
rg --type py 'GramCat\.Create\('

# Direct construction of the deprecated class:
rg --type py 'GramCatOperations\('
```

Then replace `project.GramCat.` with `project.POS.` throughout, and handle
each `Create` call per the table above. To surface remaining uses at runtime:

```bash
python -W error::DeprecationWarning your_script.py
```

### What If I Can't Migrate Yet?

Pin `pyflexicon==4.6.0`. No back-compat shim is provided, and none is planned:
the old `GramCat` write path produced incorrect data rather than different
data. Read-only callers get a longer runway -- `project.GramCat` keeps
resolving, to a deprecated wrapper over the POS list, until it is removed at
v5.0.0. Expect one `DeprecationWarning` per project in the meantime.

---

## New: the portable module shape for FlexTools modules

### What Changed

`FLExProject.FromOpenProject(donor)` is new. It returns the full flexicon facade
over a cache **someone else already opened** -- normally the project FlexTools
handed your `Main()`.

```python
from flexicon import FLExProject

def Main(project, report, modifyAllowed):
    fx = FLExProject.FromOpenProject(project)   # identical under FlexTools and the MCP
    lex, variants = fx.LexEntry, fx.Variants
```

This is the shape to write from now on. It opens nothing, closes nothing, and
behaves the same in both hosts:

- **Under FlexTools**, `project` is a *flexlibs* `FLExProject` -- the shallow
  stable wrapper, ~40 functions. `FromOpenProject` attaches a flexicon view to
  its live cache and you get the deep API.
- **Under the FlexToolsMCP runner**, `project` is *already* a flexicon
  `FLExProject`, so `FromOpenProject` returns it unchanged
  (`FromOpenProject(x) is x`). Adding the line costs nothing and changes nothing.

One module source, both hosts, no branching.

### Why This Changed -- and why `from flexicon import FLExProject` alone was never enough

Our template has told people for years to import from flexicon explicitly, with
the warning that otherwise "your code will silently use the wrong (stable)
version". Half of that was right and half of it was never true.

**Right:** the two libraries genuinely differ, and getting the shallow one when
you wanted the deep one is a real and confusing failure.

**Never true:** importing a *class* has no effect on the *instance* someone else
constructed and handed you. FlexTools builds `project` from `flexlibs` before
your module is even imported. After

```python
from flexicon import FLExProject      # binds a name in your module
```

the parameter `project` is still the flexlibs object it always was, and
`project.LexEntry` still resolves against flexlibs. The import was a dead line.
It bound a name nothing used -- which is why the old advice appeared to work:
scripts that only touched the ~40 functions both wrappers share behaved
identically, and the ones that reached further failed in ways that looked like
missing APIs rather than like a wrong object.

`FromOpenProject()` is what that import was always trying to be. It makes the
imported class load-bearing: you use it to *convert* the instance you were given,
rather than hoping the import changed it.

### Migration: rewrite the first line of `Main()`

**Before -- works under the MCP, silently shallow under FlexTools:**
```python
from flexicon import FLExProject, LexEntryOperations   # the second name is unused

def Main(project, report, modifyAllowed):
    for entry in project.LexEntry.GetAll():            # flexlibs under FlexTools
        ...
```

**After -- portable:**
```python
from flexicon import FLExProject

def Main(project, report, modifyAllowed):
    fx = FLExProject.FromOpenProject(project)
    for entry in fx.LexEntry.GetAll():                 # flexicon in both hosts
        ...
```

Then use `fx` everywhere you used `project`. To find modules still needing it:

```bash
rg --type py -l 'def Main\(project' | xargs rg -l -v 'FromOpenProject'
```

### What a view will and will not do

An attached view is a view over a cache it does not own, so the lifecycle calls
that would end the host's session are refused rather than obeyed:

| Call | On an attached view |
|---|---|
| `Transaction()` | Supported -- use it |
| `UndoableOperation()` | `FP_TransactionError`; the host holds a session-long non-undoable envelope |
| `SaveChanges()` | `FP_RuntimeError`; the host owns the save |
| `CloseProject()` | Silent no-op -- returns `None`, never raises |

**The host saves, not your module.** Just return when you are done; FlexTools
persists on close. Verified live on two projects -- see
`docs/TRANSACTION_GUIDE.md`, "Special Case: Attached View".

A donor missing `project` or `writeEnabled` raises `FP_ParameterError` naming
every absent attribute and the donor's module, instead of an `AttributeError`
fifty frames deep inside an operation.

### Resolving objects: navigate, do not resolve a bare GUID

Unrelated to the bridge, but it bites first-time users of the shape above.
`project.Object(guid)` returns the object at its **base** `ICmObject` type:

```python
sense = fx.Object("07086e7d-...")
fx.Senses.GetGloss(sense)
# AttributeError: 'ICmObject' object has no attribute 'Gloss'
```

Objects reached by navigation come back correctly typed, so prefer that and skip
the cast entirely:

```python
sense = fx.LexEntry.GetAllSenses(entry)[0]
fx.Senses.GetGloss(sense)                    # fine
```

### What If I Can't Migrate Yet?

Nothing breaks. `FromOpenProject()` is purely additive -- existing modules keep
working exactly as before, including the ones with the dead import. You only need
the new line when you want the deep API under FlexTools.

Two environment failures are worth knowing about, because neither reads as one:

- `pyflexicon` **not installed** -> `ImportError` at module import, before
  `Main()` runs. FlexTools shows a load traceback naming a package.
- `pyflexicon` installed but **predating this release** -> imports cleanly, then
  dies on the first line of `Main()` with
  `AttributeError: type object 'FLExProject' has no attribute 'FromOpenProject'`.

Both mean the module is fine and the environment is not. `pip install -U
pyflexicon` in the Python that FlexTools runs -- which is not necessarily the one
on your `PATH`. Note also that `importlib.metadata.version("pyflexicon")` can
disagree with `flexicon.version` on editable installs, so trust the capability,
not the number:

```python
hasattr(FLExProject, "FromOpenProject")   # the only reliable probe
```

---
