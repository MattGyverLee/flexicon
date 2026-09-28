# Live verification -- #276 T11

> **This file records TWO live runs.** Run 2 (below) is the run of record;
> run 1 is retained beneath it because it is what exposed the `spec.md`
> section 4 contradiction that the repo owner then ruled on. Do not delete it.

---

# Run 2 (RUN OF RECORD) -- re-verification after the ruling

**Projects:** Target (write path, demonstrations 1-4) and Sena 3 (read path, natural nesting)
**Fixtures:** `target_sandbox`, `sena3_sandbox` -- function-scoped tempdir copies of
`tests/fixtures/Target 2026-07-06 0218.fwbackup` and
`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`. The real Target is never opened
by this test file.
**run_mode:** `live`
**Date:** 2026-09-09

## Why a re-run was required

Run 1 passed 8/8 live, but on the arrangement it verified
(`FLExProject.GramCat` returning `self.POS`) the `FP_ParameterError` migration
signpost was **unreachable** through `project.GramCat` -- the exact path a
FlexTools / FlexTrans caller takes. Run 1 recorded that as a deviation. The repo
owner then ruled: **keep the raising override reachable, drop the literal `is`
identity.** The write path therefore changed, so run 1's pass no longer carries
and the gate is re-established here.

## Commands run

```
python scripts/restore_target.py
    [INFO] Removing existing C:\ProgramData\SIL\FieldWorks\Projects\Target
    [INFO] Unzipping Target 2026-07-06 0218.fwbackup -> C:\ProgramData\SIL\FieldWorks\Projects\Target
    [OK] Restored Target -> C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata

FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_276_gramcat_pos_alias.py -m requires_live_project -q -rsxw
```

Verbatim summary line:

```
8 passed, 1 warning in 7.79s
```

`-rsxw` reported no skips and no xfails: all 8 tests ran. run_mode check:

```
python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
live
```

`tests/live_status.json` additionally records all 8 tests as `status: pass`,
across `FLExProject/read`, `POSOperations/read`, `POSOperations/add` and
`GramCatOperations/add`, with `uncategorized_live_tests: []`.

## Liveness probe

As in run 1, the concrete pre/post values below were re-collected outside pytest
with a standalone script reproducing the fixture logic exactly (same
`_FwBackupSandbox` helper from `tests/conftest.py`, same
`OpenProject(writeEnabled=True, undoable=False)`), so the Hvos and counts here
are real LCM reads rather than a paraphrase of test names:

```
backup             : Target 2026-07-06 0218.fwbackup
project type       : flexicon.code.FLExProject.FLExProject
proj.project cache : LcmCache
proj.lp            : ILangProject Hvo 8870
writeEnabled       : True
```

## Claim under test

`project.GramCat` is a lazily-cached, **distinct** `GramCatOperations` (a
`POSOperations` subclass) addressing the same list as `project.POS`; the
category inventory is `lp.PartsOfSpeechOA` and never
`lp.MsFeatureSystemOA.TypesOC`; `POSOperations.GetParent` is backfilled; and
`GramCat.Create` raises `FP_ParameterError` naming the replacements, writing
nothing, **on both the property route and the direct-construction route**.

---

## Demonstration 1 -- the alias, restated (Target sandbox)

`project.GramCat is project.POS` is deliberately **no longer** asserted. What
that identity was ever a proxy for -- same type surface, same LCM list -- is
asserted instead, and the third reading (a direct walk) is what anchors it.

| Read from the live project | Value |
|---|---|
| `type(project.GramCat)` | `GramCatOperations` |
| `type(project.POS)` | `POSOperations` |
| `id(project.GramCat)` | `1434328613232` |
| `id(project.POS)` | `1434337240720` |
| `project.GramCat is project.POS` | **`False`** (was `True` in run 1) |
| `isinstance(GramCat, GramCatOperations)` | `True` |
| `isinstance(GramCat, POSOperations)` | `True` |
| MRO class supplying `.Create` | **`GramCatOperations`** (the raising override) |
| `gramcat.project is pos.project` | `True` |
| `project.GramCat is project.GramCat` (cached) | `True` |
| DeprecationWarnings on FIRST access | `1`, raised at `FLExProject.py:1799` |
| DeprecationWarnings on 2 further accesses | **`0`** (once per project, not per access) |

Same list, three independent readings:

```
GramCat.GetAll(recursive=True) hvos : 5 [2706, 5293, 6356, 6433, 6561]
POS.GetAll(recursive=True)     hvos : 5 [2706, 5293, 6356, 6433, 6561]
direct walk of lp.PartsOfSpeechOA   : 5 [2706, 5293, 6356, 6433, 6561]
GramCat == POS                      : True
GramCat == direct walk              : True
lp.MsFeatureSystemOA.TypesOC        : present=True count=0 hvos=()
overlap POS hvos vs TypesOC         : []
```

[PASS] Two distinct Python objects, one LCM collection. The `.Create` lookup
lands on `GramCatOperations`, so the migration signpost is reachable through the
property -- which is the whole point of the ruling.

---

## Demonstration 2 -- `GetAll()` yields `IPartOfSpeech`, and `recursive=True` descends

### 2a. Element type and collection identity (Target sandbox)

```
GetAll(recursive=True)     : 5 objects, ClassNames = ['PartOfSpeech']
GetAll hvos == direct walk : True
overlap with TypesOC hvos  : []   (TypesOC count=0)
```

### 2b. `recursive=True` strictly descends -- created nesting (Target sandbox)

Pre-state (LCM): 5 categories total, 4 top-level (Hvo 6356 is already a
subcategory in the stock Target).

```
PRE  total categories            : 5
PRE  top-level (recursive=False) : 4 [2706, 6561, 6433, 5293]
```

Action:

```python
root  = project.POS.Create("TEST_276_Root_A", "T276rA")                    -> Hvo 10442
sub   = project.POS.AddSubcategory(root, "TEST_276_Sub_A", "T276sA")       -> Hvo 10443
gchld = project.POS.AddSubcategory(sub, "TEST_276_Grandchild_A", "T276gA") -> Hvo 10444
```

Post-state, all re-queried from the LCM (never from the returned objects):

```
GetAll(recursive=False) : 5 hvos [2706, 6561, 6433, 5293, 10442]
GetAll(recursive=True)  : 8 hvos [2706, 6561, 6433, 6356, 5293, 10442, 10443, 10444]
names RE-READ by Hvo    : 10442='TEST_276_Root_A' 10443='TEST_276_Sub_A' 10444='TEST_276_Grandchild_A'
ClassNames re-read      : ['PartOfSpeech']
strictly-more           : 8 > 5 -> True
root  (10442)           : in flat=True
sub   (10443)           : in deep=True, in flat=False
gchld (10444)           : in deep=True, in flat=False
deep == baseline + 3    : True
```

### 2c. `recursive=True` strictly descends -- natural nesting (Sena 3 sandbox)

**`test_recursive_descends_on_sena3_natural_nesting` did NOT skip again** --
confirmed for run 2, with the same shape as run 1 (flat=11, deep=37,
`TypesOC.Count=2`, zero Hvo overlap). Read-only; nothing written.

```
GetAll(recursive=False)         : 11 hvos [21787, 42183, 50512, 58044, 65460,
                                           65501, 69519, 80535, 98110, 100407, 119927]
GetAll(recursive=True)          : 37
strictly-more                   : 37 > 11 -> True
ClassNames in the deep walk     : ['PartOfSpeech']
top-level parents with children : 4
    'Preposicao' (Preposi-c-ao, cedilla/tilde) Hvo=21787 children=[84066, 98154]          all in deep: True
    (name empty)                        Hvo=98110 children=[97023]                        all in deep: True
    (name empty)                        Hvo=65460 children=[5539, 40932, 107220, 116991]  all in deep: True
    'Verbo'                             Hvo=80535 children=[45540, 76307, 82676, 87418,
                                                            103656, 105635, 116250,
                                                            123293, 130871]               all in deep: True
lp.MsFeatureSystemOA.TypesOC    : present=True count=2 hvos=(14407, 121568)   <-- non-empty
overlap POS hvos vs TypesOC     : []                                          <-- and disjoint
```

[PASS] On a project whose feature system really does hold two
`IFsFeatStrucType`s, `GetAll` returns 37 `PartOfSpeech` objects and zero feature
types. The #276 ruling observed directly: the two collections are disjoint.

[NOTE] Two Sena 3 top-level categories still return an empty string from
`GetName` (Hvo 98110 and 65460) -- no name in the default analysis writing
system. Unchanged from run 1, not part of the #276 ruling, no action taken.

---

## Demonstration 3 -- `POS.GetParent` round-trips, and is `None` at top level

### 3a. Round-trip against `AddSubcategory` (Target sandbox)

The subcategory is re-queried from the LCM by Hvo through
`GetAll(recursive=True)`; the object `AddSubcategory` returned is discarded.

```
GetParent(re-read sub Hvo=10443)
    -> Hvo=10442  ClassName='PartOfSpeech'  Name='TEST_276_Root_A'   (expected root Hvo=10442)
parent.SubPossibilitiesOS.Count            : 1     (subtype-only member -- proves the cast)
GetSubcategories(parent, recursive=False)  : [10443]
GetParent of each of those                 : [10442]   (inverts GetSubcategories)
```

### 3b. `None` for a top-level category (Target sandbox)

```
top-level root Hvo=10442, LCM Owner.ClassName = 'CmPossibilityList'
GetParent(top-level root)  ->  None
```

### 3c. The same on pre-existing Sena 3 data

```
GetParent(pre-existing child Hvo=84066)     -> Hvo=21787  ClassName='PartOfSpeech'  (owner is 21787)
GetParent(pre-existing top-level Hvo=21787) -> None
```

[PASS] Unchanged from run 1, on freshly created and on pre-existing categories.

---

## Demonstration 4 -- `GramCat.Create(...)` raises and writes NOTHING, on BOTH routes

**The regression that matters most: the retired implementation added a stray
`IFsFeatStrucType` to `lp.MsFeatureSystemOA.TypesOC` on every call.** Hvo
**sets/lists** are compared, not just counts, so a same-count swap is caught.

### 4a. Through the `project.GramCat` property -- the newly reachable route

This is what run 1 could not demonstrate: the property route then raised a bare
`TypeError`. It now raises the migration pointer.

```
PRE  lp.PartsOfSpeechOA (list order)  : 5 [2706, 6561, 6433, 6356, 5293]
PRE  lp.MsFeatureSystemOA.TypesOC     : present=True count=0 hvos=()

action: project.GramCat.Create("TEST_276_alias_create")
raised                                : FP_ParameterError      <-- was TypeError in run 1
  names project.POS.Create            : True
  names project.POS.AddSubcategory    : True

POST lp.PartsOfSpeechOA (list order)  : 5 [2706, 6561, 6433, 6356, 5293]
POST lp.MsFeatureSystemOA.TypesOC     : present=True count=0 hvos=()
PartsOfSpeech identical pre vs post   : True
TypesOC identical pre vs post         : True
```

### 4b. Directly-constructed `GramCatOperations`, both legacy call shapes

Construction emits the `DeprecationWarning` (1 recorded).

```
PRE  lp.PartsOfSpeechOA               : 5 [2706, 6561, 6433, 6356, 5293]
PRE  lp.MsFeatureSystemOA.TypesOC     : present=True count=0 hvos=()
```

| # | Call | Raised | TypesOC after | PartsOfSpeech after |
|---|------|--------|---------------|---------------------|
| 1 | `GramCatOperations(proj).Create("TEST_276_gramcat_create")` | `FP_ParameterError` | count=0 hvos=() **unchanged** | 5, same Hvo list **unchanged** |
| 2 | `...Create("TEST_276_gramcat_create_child", parent=2706)` | `FP_ParameterError` (names `AddSubcategory`) | count=0 hvos=() **unchanged** | 5, same Hvo list **unchanged** |

```
POST lp.PartsOfSpeechOA               : 5 [2706, 6561, 6433, 6356, 5293]
POST lp.MsFeatureSystemOA.TypesOC     : present=True count=0 hvos=()
PartsOfSpeech identical pre vs post   : True
TypesOC identical pre vs post         : True
alias-route message == direct-route message : True
```

The `FP_ParameterError` message, verbatim from the live raise (identical on both
routes):

```
GramCat.Create() has been removed (issue #276): it never created a grammatical
category. It created a stray IFsFeatStrucType in the feature system
(LangProject.MsFeatureSystemOA.TypesOC), which is a structural template for
feature structures, not a category. A list-level grammatical category is a Part
of Speech: use project.POS.Create(name, abbreviation) for a top-level category,
or project.POS.AddSubcategory(parent, name, abbreviation) for a subcategory. If
you did want a feature-structure type, use
project.InflectionFeatures.TypeCreate(name, abbreviation).
```

[PASS] Both routes raise before any write. `TypesOC` is count=0 with identical
(empty) Hvo membership before and after; the `PartsOfSpeechOA` Hvo list is
element-for-element the same list. No category and no feature-structure type
created.

---

## Run 1's recorded deviation from `spec.md` section 4 -- now CLOSED

Run 1 recorded that `project.GramCat.Create("x")` raised a bare
`TypeError` about a missing `abbreviation` argument instead of the
`FP_ParameterError`, because `FLExProject.GramCat` returned `self.POS`.
Demonstration 4a above shows that path now raising `FP_ParameterError` naming
both replacements. The deviation is resolved, and the resolution is the one the
repo owner ruled for: distinct cached subclass, no literal `is` identity.

[NOTE] Consequently `project.GramCat is project.POS` is now `False`. Any
documentation asserting the identity (`spec.md` sections 2/3, and any
MIGRATION_GUIDE text written under T12) must say *addresses the same list*, not
*is the same object*.

## Cleanup

- All 8 pytest tests ran against **tempdir sandboxes**; the real Target and the
  real Sena 3 were never opened by the test file.
- Within the Target sandbox the created hierarchy was deleted and the state
  re-read: `POST-cleanup direct walk : 5 hvos [2706, 6561, 6433, 6356, 5293]`,
  identical to the pre-state, and `TypesOC` still `count=0 hvos=()`. So
  `POSOperations.Delete` does remove the whole subtree, and the two
  `[NOTE] cleanup check` assertions passed.
- Real Target checked after the run: `grep -c TEST_276` against
  `C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata` -> `0`.
  No `TEST_` leakage.
- No sandbox tempdirs left behind.
- `python scripts/restore_target.py` was run before verification; the Target is
  at its golden baseline.

## Warnings summary (expected, not a failure)

```
tests/operations/test_276_gramcat_pos_alias.py::TestGramCatGetAllYieldsPartsOfSpeech::test_getall_elements_are_partofspeech_not_featstructype
  flexicon\code\FLExProject.py:1799: DeprecationWarning: GramCatOperations is a
  deprecated alias for POSOperations; ...
```

That test does a bare `target_sandbox.GramCat` without `pytest.warns`, so the
alias warning surfaces unhandled. There is no `filterwarnings = error` in this
repo, so it does not fail the run. It is in fact corroborating evidence for
demonstration 1: the warning is raised from the property at
`FLExProject.py:1799`, exactly once.

## Supplementary -- mock regression suite

```
python -m pytest -m "not requires_live_project" -q
1748 passed, 710 deselected, 12 warnings, 5 subtests passed in 25.44s
```

**Clean.** Run 1's single failure --
`tests/test_lcm_method_verification.py::TestLCMMethodVerification::test_all_factory_creates_have_service_locator`,
a lint heuristic that flagged the literal `.Create()` inside the
`FP_ParameterError` prose -- is fixed: the heuristic now blanks string literals
and comments via `tokenize` rather than only triple-quoted docstrings. That file
passes on its own too (`10 passed`). The #276 error text was NOT weakened.

[NOTE] Scope of the command matters. `python -m pytest tests/ -m "not
requires_live_project" -q` collects less (`1545 passed, 581 deselected`) because
it omits the suites outside `tests/` (e.g. `flexicon/sync/tests/`). The figure
above uses the same rootdir-wide invocation as run 1 so the two are comparable.
The `-m` filter is present in both; bare `pytest` was never run.

## Result

**[PASS]** -- run_mode `live`; all four #276 demonstrations re-observed against a
real LCM after the write-path change, with pre/post values re-read from the
database and Hvo sets (not just counts) compared; the alias route now reaches the
`FP_ParameterError` signpost; sandboxes clean, no leakage; mock suite clean.

---

# Run 1 (SUPERSEDED, retained deliberately) -- the run that exposed the flaw

> Superseded by run 2 above, which re-verified the write path after the
> repo owner's ruling. Kept verbatim because run 1 is the evidence that
> `spec.md` section 4's `FP_ParameterError` and sections 2/3's
> `project.GramCat is project.POS` were mutually exclusive -- it observed
> the `TypeError` on the alias route live. Its Demonstration 1 table
> (`GramCat is POS -> True`) and its "Deviation" section describe the
> PRE-RULING code and no longer describe HEAD.

**Projects:** Target (write path, all four demonstrations) and Sena 3 (read path, natural nesting)
**Fixtures:** `target_sandbox`, `sena3_sandbox` -- function-scoped tempdir copies of
`tests/fixtures/Target 2026-07-06 0218.fwbackup` and
`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`. The real Target is never opened
by this test file.
**run_mode:** `live`
**Date:** 2026-09-09

## Commands run

```
python scripts/restore_target.py
    [INFO] Removing existing C:\ProgramData\SIL\FieldWorks\Projects\Target
    [INFO] Unzipping Target 2026-07-06 0218.fwbackup -> C:\ProgramData\SIL\FieldWorks\Projects\Target
    [OK] Restored Target -> C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata

FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_276_gramcat_pos_alias.py -m requires_live_project -q
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_276_gramcat_pos_alias.py -m requires_live_project -v -rsx
```

Verbatim summary line:

```
8 passed in 8.02s
```

(second, verbose run: `============================== 8 passed in 8.17s ==============================`,
all 8 reported `PASSED`, zero skipped, `-rsx` printed no skip/xfail reasons.)

run_mode check:

```
python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
live
```

## Liveness probe

The pre/post values below were additionally re-collected outside pytest with a
standalone script that reproduces the fixture logic exactly (unzip the same
`.fwbackup` to a tempdir, `OpenProject(writeEnabled=True, undoable=False)`), so
the concrete Hvos and counts in this file are real LCM reads rather than a
paraphrase of test names. That script confirmed:

```
project type       : flexicon.code.FLExProject.FLExProject
proj.project cache : LcmCache
proj.lp            : ILangProject Hvo 8870
writeEnabled       : True
```

## Claim under test

`project.GramCat` becomes a discoverability alias onto `POSOperations`; the
category inventory is `lp.PartsOfSpeechOA` and never
`lp.MsFeatureSystemOA.TypesOC`; `POSOperations.GetParent` is backfilled; and
the old `GramCat.Create` write into the feature system is gone.

---

## Demonstration 1 -- `project.GramCat is project.POS`

**Project:** Target sandbox.

| Read from the live project | Value |
|---|---|
| `type(project.GramCat)` | `POSOperations` |
| `id(project.GramCat)` | `1709319909264` |
| `id(project.POS)` | `1709319909264` |
| `project.GramCat is project.POS` | `True` |
| `isinstance(project.GramCat, POSOperations)` | `True` |
| `project.GramCat is project.GramCat` (stability) | `True` |

[PASS] One object, one CRUD surface over `lp.PartsOfSpeechOA`.

---

## Demonstration 2 -- `GetAll()` yields `IPartOfSpeech`, and `recursive=True` descends

### 2a. Element type and collection identity (Target sandbox)

Pre-state, read from the LCM:

```
direct depth-first walk of lp.PartsOfSpeechOA : 5 hvos [2706, 6561, 6433, 6356, 5293]
lp.MsFeatureSystemOA.TypesOC                  : present=True count=0 hvos=[]
```

Action: `project.GramCat.GetAll(recursive=True)`.

Post-state, read back:

```
GetAll(recursive=True)        : 5 objects, ClassNames = ['PartOfSpeech']
GetAll hvos == direct walk    : True
overlap with TypesOC hvos     : []   (empty)
```

[PASS] Every element is a `PartOfSpeech`; the set matches an independent direct
walk of `lp.PartsOfSpeechOA`; nothing came from the feature system.

### 2b. `recursive=True` strictly descends -- created nesting (Target sandbox)

**This is the demonstration of record for the created-nesting half.**

Pre-state (LCM): 5 categories total, 4 of them top-level (Hvo 6356 is already a
subcategory in the stock Target).

Action:

```python
root  = project.POS.Create("TEST_276_Root_A", "T276rA")                 -> Hvo 10442
sub   = project.POS.AddSubcategory(root, "TEST_276_Sub_A", "T276sA")    -> Hvo 10443
gchld = project.POS.AddSubcategory(sub, "TEST_276_Grandchild_A", "T276gA") -> Hvo 10444
```

Post-state, all re-queried from the LCM (never from the returned objects):

```
GetAll(recursive=False) : 5 hvos [2706, 6561, 6433, 5293, 10442]
GetAll(recursive=True)  : 8 hvos [2706, 6561, 6433, 6356, 5293, 10442, 10443, 10444]
names re-read by Hvo    : 10442='TEST_276_Root_A'  10443='TEST_276_Sub_A'  10444='TEST_276_Grandchild_A'
strictly-more           : 8 > 5  -> True
sub  (10443)            : in deep=True,  in flat=False
grandchild (10444)      : in deep=True,  in flat=False
```

[PASS] Recursion reaches two levels down. The retired `TypesOC` implementation
could not do this -- `IFsFeatStrucType` has no `SubPossibilitiesOS`.

### 2c. `recursive=True` strictly descends -- natural nesting (Sena 3 sandbox)

**`test_recursive_descends_on_sena3_natural_nesting` did NOT skip.** Sena 3 does
carry nested categories, so item 2 is carried by BOTH tests; this one is the
stronger of the two because Sena 3's feature system is non-empty.

Read from the LCM (read-only, nothing written):

```
GetAll(recursive=False)         : 11 hvos [21787, 42183, 50512, 58044, 65460,
                                           65501, 69519, 80535, 98110, 100407, 119927]
GetAll(recursive=True)          : 37
strictly-more                   : 37 > 11 -> True
ClassNames in the deep walk     : ['PartOfSpeech']
top-level parents with children : 4
    'Preposic\u0327a\u0303o' Hvo=21787  children=[84066, 98154]                    all in deep walk: True
    (name empty)             Hvo=98110  children=[97023]                           all in deep walk: True
    (name empty)             Hvo=65460  children=[5539, 40932, 107220, 116991]     all in deep walk: True
    'Verbo'                  Hvo=80535  children=[45540, 76307, 82676, 87418,
                                                  103656, 105635, 116250,
                                                  123293, 130871]                  all in deep walk: True
lp.MsFeatureSystemOA.TypesOC    : count=2      <-- non-empty here
overlap POS hvos vs TypesOC     : []           <-- and still disjoint
```

[PASS] On a project whose feature system actually holds two `IFsFeatStrucType`s,
`GetAll` returns 37 `PartOfSpeech` objects and zero feature types. That is the
#276 ruling observed directly: the two collections are disjoint.

[NOTE] Two Sena 3 top-level categories return an empty string from `GetName`
(Hvo 98110 and 65460) -- no name in the default analysis writing system. Not
part of the #276 ruling, observed in passing, no action taken.

---

## Demonstration 3 -- `POS.GetParent` round-trips, and is `None` at top level

### 3a. Round-trip against `AddSubcategory` (Target sandbox)

The subcategory is re-queried from the LCM by Hvo through
`GetAll(recursive=True)` before `GetParent` is called; the object
`AddSubcategory` returned is deliberately discarded.

```
GetParent(re-read sub Hvo=10443)
    -> Hvo=10442  ClassName='PartOfSpeech'  Name='TEST_276_Root_A'   (expected root Hvo=10442)
parent.SubPossibilitiesOS.Count            : 1     (subtype-only member -- proves the cast)
GetSubcategories(parent, recursive=False)  : [10443]
GetParent of each of those                 : [10442]   (inverts GetSubcategories)
```

### 3b. `None` for a top-level category (Target sandbox)

```
top-level root Hvo=10442, LCM Owner.ClassName = 'CmPossibilityList'
GetParent(top-level root)  ->  None
```

The owner really is the `ICmPossibilityList` at `lp.PartsOfSpeechOA`, which is
not a possibility -- so `None` is correct, and no exception is raised.

### 3c. The same on pre-existing Sena 3 data (not just objects this run created)

```
GetParent(pre-existing child Hvo=84066)     -> Hvo=21787  ClassName='PartOfSpeech'  (owner is 21787)
GetParent(pre-existing top-level Hvo=21787) -> None
```

[PASS] The T2 backfill round-trips both directions, on freshly created and on
pre-existing categories.

---

## Demonstration 4 -- `GramCat.Create(...)` raises and writes NOTHING

**This is the regression that matters most: the old implementation added a stray
`IFsFeatStrucType` to `lp.MsFeatureSystemOA.TypesOC` on every call.**

Pre-state, read from the LCM:

```
lp.MsFeatureSystemOA.TypesOC : present=True  count=0  hvos=[]
lp.PartsOfSpeechOA deep walk : 5 hvos [2706, 6561, 6433, 6356, 5293]
```

Construction of the deprecated class emits, as required:

```
DeprecationWarning: GramCatOperations is a deprecated alias for POSOperations;
use project.POS (or POSOperations directly) instead. A list-level grammatical
category is a Part of Speech; the feature-structure types this class used to
walk live at project.InflectionFeatures (issue #276).
```

Three call shapes were exercised, with both collections re-read after each:

| # | Call | Raised | TypesOC after | PartsOfSpeech after |
|---|------|--------|---------------|---------------------|
| 1 | `GramCatOperations(proj).Create("TEST_276_gramcat_create")` | `FP_ParameterError` | count=0 hvos=[] **unchanged** | 5 **unchanged** |
| 2 | `GramCatOperations(proj).Create("TEST_276_gramcat_create_child", parent=2706)` | `FP_ParameterError` | count=0 hvos=[] **unchanged** | 5 **unchanged** |
| 3 | `project.GramCat.Create("TEST_276_alias_create")` (alias route) | `TypeError` -- see deviation below | count=0 hvos=[] **unchanged** | 5 **unchanged** |

The `FP_ParameterError` message, verbatim from the live raise:

```
GramCat.Create() has been removed (issue #276): it never created a grammatical
category. It created a stray IFsFeatStrucType in the feature system
(LangProject.MsFeatureSystemOA.TypesOC), which is a structural template for
feature structures, not a category. A list-level grammatical category is a Part
of Speech: use project.POS.Create(name, abbreviation) for a top-level category,
or project.POS.AddSubcategory(parent, name, abbreviation) for a subcategory. If
you did want a feature-structure type, use
project.InflectionFeatures.TypeCreate(name, abbreviation).
```

Post-state after all three raising calls, re-read from the LCM:

```
lp.MsFeatureSystemOA.TypesOC : count=0  hvos=[]
lp.PartsOfSpeechOA deep walk : 5 hvos [2706, 6561, 6433, 6356, 5293]
TypesOC identical pre vs post       : True
PartsOfSpeech identical pre vs post : True
```

[PASS] `TypesOC.Count` is 0 before and 0 after, with identical Hvo membership
(so a same-count swap would also have been caught). No category was created
either. The feature-system corruption path is gone.

---

## Deviation from `spec.md` section 4 -- stated plainly

`spec.md` section 4 says "`GramCat.Create` therefore raises `FP_ParameterError`
naming `project.POS.Create(name, abbreviation)` and
`project.POS.AddSubcategory(parent, name, abbreviation)`."

**Observed live, that is true only of the class, not of the property.** Because
T3 made `FLExProject.GramCat` `return self.POS`, `project.GramCat.Create("x")`
never reaches the `GramCatOperations.Create` override at all. It binds against
`POSOperations.Create(name, abbreviation)` and raises:

```
TypeError: POSOperations.Create() missing 1 required positional argument: 'abbreviation'
```

The `FP_ParameterError` with its helpful pointer is reachable only by
instantiating `GramCatOperations(project)` directly -- which itself emits a
`DeprecationWarning`. Both routes were exercised above and **neither writes
anything**, so the safety property #276 cares about holds on both paths. What
differs is the *diagnostic quality* on the path an existing FlexTools caller
will actually take: an unmigrated `project.GramCat.Create("Transitive")` gets a
bare `TypeError` naming a missing argument, not the migration pointer that names
`project.POS.Create` / `project.POS.AddSubcategory`.

Recorded, not papered over. Whether to close that gap (for example by having
`FLExProject.GramCat` keep returning `POSOperations` while the migration text is
surfaced some other way) is a design call for the lead, not something T11
decides. The MIGRATION_GUIDE entry written under T12 should not imply callers
will see the `FP_ParameterError`.

---

## Cleanup

- All 8 pytest tests ran against **tempdir sandboxes**; the real Target and the
  real Sena 3 were never opened by the test file.
- Real Target checked after the run: `grep -c "TEST_276" Target.fwdata` -> `0`.
  No `TEST_` leakage.
- Within the Target sandbox, the created hierarchy was deleted and the state
  re-read: `POST-cleanup direct walk : 5 hvos [2706, 6561, 6433, 6356, 5293]`,
  identical to the pre-state -- so `POSOperations.Delete` does remove the whole
  subtree, and the two `[NOTE] cleanup check` assertions in the test file passed.
- No sandbox tempdirs left behind (verified empty after the run).
- `python scripts/restore_target.py` was run before verification; the Target is
  at its golden baseline.

## Supplementary -- mock regression suite

```
python -m pytest -m "not requires_live_project" -q
1 failed, 1747 passed, 710 deselected, 12 warnings, 5 subtests passed in 29.56s
```

The single failure is **caused by this change** and must be triaged before merge:

```
FAILED tests/test_lcm_method_verification.py::TestLCMMethodVerification::test_all_factory_creates_have_service_locator
AssertionError: flexicon\code\Grammar\GramCatOperations.py: Create() should be on factory from GetService
```

It is a heuristic false positive, not a functional defect. The test strips
docstrings and then requires any file containing the literal `.Create()` to also
contain `GetService(`. After T4 the only `.Create()` left in
`GramCatOperations.py` is prose inside the `FP_ParameterError` message at
`flexicon/code/Grammar/GramCatOperations.py:154`
(`"GramCat.Create() has been removed (issue #276): it never "`), and the file no
longer resolves any factory, so `GetService(` is legitimately absent. The
pre-change file contained 5 `GetService(` calls, which is why this passed at
HEAD. Fix belongs with the programmer: either exempt the file, teach the
heuristic to ignore string literals as it already ignores docstrings, or reword
the message. Do not weaken the #276 error text just to satisfy a lint.

## Result

**[PASS]** -- run_mode `live`; all four #276 demonstrations observed against a
real LCM with pre/post values re-read from the database; sandboxes clean; one
supplementary mock-suite lint failure introduced by the change, and one
diagnostic-quality deviation from `spec.md` section 4, both recorded above.
