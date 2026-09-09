# live-277-overlays.md -- OverlayOperations half of issue #277

Scope: `flexicon/code/Lists/OverlayOperations.py:GetPossItems`. The
`EnvironmentOperations.py` half of #277 is owned by a different,
concurrently running agent and is NOT covered by this file (see
`live-277-environments.md`).

## Commands run (verbatim)

Live `.NET` reflection (no project needs to be open for this part --
`SIL.LCModel` just needs to be loadable):

```
python <ad-hoc reflection script bootstrapping FieldWorks paths + clr.AddReference("SIL.LCModel")>
```

RED (unmodified source, `OverlayOperations.py` temporarily reverted via
`git stash push -- flexicon/code/Lists/OverlayOperations.py`):

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_overlay_operations.py -m requires_live_project -q
```

GREEN (fix restored via `git stash pop`, identical command):

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_overlay_operations.py -m requires_live_project -q
```

Both runs executed against `sena3_sandbox` (a fresh tempdir copy of the
Sena 3 `.fwbackup`, restored per-test -- never the user's real Sena 3).

## `tests/live_status.json` run_mode (verbatim, GREEN run)

```
python -c "import json; print(json.load(open('tests/live_status.json'))['run_mode'])"
-> live
```

If this had printed `mock`, none of the below would count as verification;
it did not.

## Step 0: premise check -- what type actually reaches `GetPossItems`

Live `.NET` reflection, `clr.GetClrType(SIL.LCModel.ICmOverlay)`:

```
Is ICmOverlay a subtype of ICmPossibility? False
ICmOverlay declared (own) public properties:
    Name
    PossItemsRC
    PossListRA
ICmOverlay direct interfaces:
    SIL.LCModel.ICmObject
    SIL.LCModel.ICmObjectOrId
```

This matches the issue's premise exactly: ICmOverlay's complete
own-declared property surface is `Name, PossItemsRC, PossListRA`, and it
is **not** an `ICmPossibility` at all (`ICmPossibility.IsAssignableFrom
(ICmOverlay)` is `False` at the CLR level) -- despite
`OverlayOperations` extending `PossibilityItemOperations` and every
method's docstring reading "overlay_or_hvo: Either an ICmPossibility
object or its HVO."

Live reflection of a real overlay object obtained via
`project.lp.OverlaysOC` (Sena 3 has exactly 1 pre-existing overlay --
see Step 1) confirms the same thing at the object level, not just the
type level:

```
type(overlay) = <class 'SIL.LCModel.ICmOverlay'>
overlay.ClassName = CmOverlay
hasattr(overlay, 'SubPossibilitiesOS') = False
hasattr(overlay, 'PossItemsRC') = True
```

Full `dir(overlay)` (public members only), captured live:
```
AllOwnedObjects, AllReferencedObjects, Cache, CanDelete, CheckConstraints,
ChooserNameTS, ClassID, ClassName, Delete, DeletionTextTSS, Equals,
GetHashCode, GetObject, GetType, Guid, Hvo, Id, IndexInOwner,
IsFieldRelevant, IsFieldRequired, IsOwnedBy, IsValidObject, MergeObject,
Name, ObjectIdName, OwnOrd, OwnedObjects, Owner, OwnerOfClass,
OwningFlid, PossItemsRC, PossListRA, PostClone, ReferenceTargetCandidates,
ReferenceTargetOwner, ReferringObjects, Self, Services, ShortName,
ShortNameTSS, SortKey, SortKey2, SortKey2Alpha, SortKeyWs, ToString,
(plus get_*/set_* accessor pairs for the above)
```

**Verdict on the premise:** the object reaching `GetPossItems` when
obtained the "real" way (from `project.lp.OverlaysOC`, an
`ILcmOwningCollection<ICmOverlay>` -- see Step 2 finding below) is a
genuine, fully-typed `ICmOverlay`, so `PossItemsRC` is directly
reachable via `hasattr`/attribute access with no cast needed. The
one-line property-name fix is sufficient **for the object-in-hand
calling convention**. The HVO-argument branch of
`_PossibilityItemOperations__ResolveObject` (int input ->
`cast_to_concrete`) has no `"CmOverlay"` entry in
`lcm_casting.py`'s `_interface_cache`, so an HVO argument would still
silently return `[]` after this fix -- but there is currently no
working path anywhere in `OverlayOperations`'s own API that could hand
a caller an overlay HVO to round-trip back in (see Step 2), so this is
recorded as a **finding**, not fixed here (same reasoning as the sibling
`EnvironmentOperations` evidence file's Step-4/TestP4 finding for the
HVO-parent gap in `BaseOperations._GetObject`).

## Step 1: does a live overlay exist to test against

**Yes.** Sena 3 (`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`, via
`sena3_sandbox`) ships with exactly **one** pre-existing `ICmOverlay`
in `project.lp.OverlaysOC`, carrying **859** items in `PossItemsRC`.
This is real production-shaped data, not something manufactured for
this task -- it made the RED/GREEN distinction unambiguous:

- RED (`SubPossibilitiesOS`, unmodified): `GetPossItems(overlay)` == `[]`
- GREEN (`PossItemsRC`, fixed): `GetPossItems(overlay)` == all 859 items,
  `{o.Hvo for o in result} == {o.Hvo for o in overlay.PossItemsRC}`

Target (the other live project) was not checked for overlays because
Sena 3 already settled the question with real data; per CLAUDE.md,
Sena 3 -- not Target -- is the populated project for read-path coverage
of this kind.

## Step 2: `_get_list_object()` verdict

**Correct-by-design given the real element type, but the surrounding
class is far more broken than issue #277 states.** Independent live
`.NET` reflection (assembly-wide property scan for `*verlay*`) found:

```
Found 2 'overlay' property hits across assembly:
    SIL.LCModel.ILangProject.OverlaysOC
        -> ILcmOwningCollection<ICmOverlay>
    SIL.LCModel.DomainImpl.LangProject.OverlaysOC   (same property, impl class)
```

`IDsConstChart` (checked directly, and via every interface it
implements -- `IDsChart`, `ICmMajorObject`, `ICmObject`,
`ICmObjectOrId`) has **no** `OverlaysOC`, `Overlays`, or any
`*Overlay*`-named member anywhere in its interface hierarchy.
`ICmOverlay` itself (Step 0) has no chart-reference property either.

This means: **overlays are not chart-scoped at all.** They are owned
project-wide, directly on `ILangProject.OverlaysOC` -- structurally the
same kind of top-level list as `ConfidenceLevelsOA` or
`PublicationsOS`, except an owning collection of `ICmOverlay` rather
than a `CmPossibilityList` of `ICmPossibility`. `PossListRA` (the third
own-declared property) is a reference to *which* possibility list an
overlay's `PossItemsRC` entries are drawn from -- i.e. an overlay is a
saved, named subset of items from some other list, used to
highlight/filter a chart display, not a child of any one chart.

Given that, `_get_list_object()` returning `None` is defensible as a
literal answer to "is there a `CmPossibilityList`-shaped list object
backing overlays" (there is not), but the practical consequence,
confirmed by re-reading the base class contract in
`possibility_item_base.py`, is that essentially the entire inherited
CRUD surface is non-functional for `OverlayOperations`, independent of
and pre-dating the `GetPossItems` bug:

- `Create()` -- unconditionally raises `FP_ParameterError` (`list_obj`
  falsy), despite being documented in this class's own docstring usage
  example (`overlay = overlay_ops.Create("Participants")`).
- `GetAll()` -- returns `[]` unconditionally (`list_obj` falsy), same
  "always empty" defect shape as the one #277 reports for
  `GetPossItems`, just in a sibling inherited method.
- `Delete()` / `Duplicate()` -- silent no-ops (`if list_obj and ...`
  short-circuits on `None`).
- `Find()` / `Exists()` -- always return `None` / `False` (call
  `GetAll()`).
- `GetName()` / `SetName()` / `GetDescription()` / `SetDescription()` /
  `CompareTo()` / `GetSyncableProperties()` -- would all raise
  `AttributeError` on a real overlay object, because `ICmOverlay.Name`
  is a plain `System.String` (confirmed live, Step 0's property-type
  reflection), not an `IMultiString`/`IMultiUnicode` -- these methods
  all call `.Name.get_String(wsHandle)` / `.Name.set_String(...)`,
  which do not exist on `System.String`. `ICmOverlay` also has **no**
  `Description` property at all (confirmed absent from both its
  own-declared surface and its base `ICmObject` surface).
- `FindByChart()` / `GetVisibleOverlays()` -- `chart.OverlaysOC` does
  not exist on `IDsConstChart` (confirmed above), so `FindByChart`
  always returns `[]`, and `GetVisibleOverlays` (which calls
  `FindByChart`) always returns `[]` too.
- `GetChart()` -- the `OwnerOfClass(DsConstChartTags.kClassId)` fallback
  at line ~437 will correctly return `None` for every overlay, because
  overlays are owned by `ILangProject`, not by any `IDsConstChart` --
  but this makes the method's entire premise (and the `#149` comment
  above it claiming chart-based ownership) incorrect, not merely
  incomplete.

**Consequence for this task's scope:** there is currently no working
path through `OverlayOperations`'s own public API that produces a live
`ICmOverlay` object to hand to `GetPossItems` -- `Create()` throws,
`GetAll()`/`Find()`/`FindByChart()` all return empty. The regression
tests below therefore construct/locate overlays directly via the LCM
(`project.lp.OverlaysOC` / `ICmOverlayFactory`), exactly as any real
caller is forced to do today, and exercise only `GetPossItems()`
through the `OverlayOperations` instance.

**This is out of scope for the one-line #277 fix and is being reported
as a separate finding, not folded in here** (see "Finding" section
below), per the task's explicit instruction not to silently expand
scope.

## Step 3: applying the fix

Changed `flexicon/code/Lists/OverlayOperations.py:GetPossItems` from:

```python
if hasattr(overlay, "SubPossibilitiesOS"):
    return list(overlay.SubPossibilitiesOS)
return []
```

to:

```python
if hasattr(overlay, "PossItemsRC"):
    return list(overlay.PossItemsRC)
return []
```

`PossItemsRC` is `ILcmReferenceCollection<ICmPossibility>` -- a
reference *collection*, not a sequence. Confirmed live that
`list(overlay.PossItemsRC)` materialises it correctly (see RED/GREEN
results below), consistent with the house pattern already established
for another `*RC` property: `list(allomorph.PhoneEnvRC)` in
`AllomorphOperations.py:1211`.

The docstring's stated return type ("list: List of associated
possibility items") stays accurate -- `GetPossItems` still returns a
plain Python `list`, just materialised from a reference collection
instead of an (nonexistent) owning sequence.

## RED result (verbatim, unmodified source)

```
2 failed, 1 passed, 1 deselected in 9.76s
FAILED tests/operations/test_overlay_operations.py::TestGetPossItemsLive::test_returns_real_items_for_preexisting_overlay
FAILED tests/operations/test_overlay_operations.py::TestGetPossItemsLive::test_returns_seeded_items_for_freshly_created_overlay
```

Failure body (seeded-overlay test):

```
result = overlay_ops.GetPossItems(overlay)
>   assert len(result) == 2, (...)
E   AssertionError: Expected 2 seeded items, GetPossItems() returned 0.
E   assert 0 == 2
E    +  where 0 = len([])
```

`test_returns_empty_list_for_overlay_with_no_items` still passed on the
unmodified source, as expected -- `[]` is the correct answer for a
genuinely empty overlay both before and after the fix, so that test
alone cannot distinguish "fixed" from "always broken" (that
distinction is exactly what the other two tests are for).

## GREEN result (verbatim, fix applied)

```
...                                                                      [100%]
3 passed, 1 deselected in 12.68s
```

`tests/live_status.json` `by_class.OverlayOperations` after the GREEN
run:

```json
"add": {
  "last_verified": "2026-09-09",
  "status": "pass",
  "tests": [
    "...test_returns_seeded_items_for_freshly_created_overlay",
    "...test_returns_empty_list_for_overlay_with_no_items"
  ]
},
"read": {
  "last_verified": "2026-09-09",
  "status": "pass",
  "tests": ["...test_returns_real_items_for_preexisting_overlay"]
}
```

## Pre-state / post-state re-queried from the LCM

**Pre-existing overlay (read-only test):**
- Pre-state: `overlay.PossItemsRC` on the real (sandbox-copied)
  pre-existing Sena 3 overlay, re-queried live: 859 `ICmPossibility`
  items.
- Action: `project.Overlays.GetPossItems(overlay)`.
- Post-state: result re-compared against a **second, independent**
  `list(overlay.PossItemsRC)` materialisation (not the same Python list
  object) by `Hvo` set equality -- exact match, 859/859.
- No mutation performed; this overlay was left untouched.

**Freshly-created overlay (seeded):**
- Pre-state: created via `ICmOverlayFactory.Create()` +
  `lp.OverlaysOC.Add(overlay)` inside a transaction, seeded with 2 real
  `ICmPossibility` items borrowed from `lp.ConfidenceLevelsOA
  .PossibilitiesOS` (confirmed live to have 4 items in the Sena 3
  fixture, well above the 2 needed).
- Action: `project.Overlays.GetPossItems(overlay)`.
- Post-state: result's `Hvo` set compared against the 2 seed items'
  `Hvo` set -- exact match.
- Cleanup: overlay removed from `lp.OverlaysOC` in a `finally:` block,
  inside its own transaction; `sena3_sandbox` is additionally a
  disposable per-test tempdir copy regardless.

**Empty overlay:**
- Pre-state: created via the same factory path, deliberately left with
  zero `PossItemsRC` entries.
- Action: `project.Overlays.GetPossItems(overlay)`.
- Post-state: `== []`.
- Cleanup: same as above.

## Pass/fail line

**PASS (property-name fix, live-verified):** `OverlayOperations
.GetPossItems` now reads `overlay.PossItemsRC` instead of the
nonexistent `overlay.SubPossibilitiesOS`, confirmed correct by live
`.NET` reflection (Step 0) and by the regression test failing on the
old code (RED, 0 items) / passing on the fix (GREEN, 859 items against
a real pre-existing overlay, and 2/2 against freshly seeded ones).

**FINDING, not a defect in scope for #277 (recommend filing
separately):** `OverlayOperations` is built on two false premises
beyond the one this issue names:
1. It extends `PossibilityItemOperations`, but `ICmOverlay` is not an
   `ICmPossibility` and its `Name` is a plain `System.String`, not a
   multilingual string type -- so `Create`, `GetAll`, `Delete`,
   `Duplicate`, `Find`, `Exists`, `GetName`, `SetName`,
   `GetDescription`, `SetDescription`, `CompareTo`, and
   `GetSyncableProperties` are all either silently no-op/empty or
   throw `AttributeError` against a real overlay.
2. `FindByChart`, `GetVisibleOverlays`, and the `OwnerOfClass` fallback
   in `GetChart` assume overlays are chart-owned
   (`IDsConstChart.OverlaysOC`, per the `#149` comment at
   `OverlayOperations.py:433-434`). Live reflection confirms overlays
   are instead owned project-wide via `ILangProject.OverlaysOC`, and
   `IDsConstChart` has no overlay-related member anywhere in its
   interface hierarchy. `FindByChart` therefore always returns `[]`,
   independent of the `GetPossItems` bug and unaffected by this fix
   either way.

Together, these mean the entire `OverlayOperations` class is
non-functional end-to-end except for the narrow `GetPossItems` path
fixed here (which had to be exercised by constructing overlays
directly via the LCM, bypassing the class's own broken `Create`).
This is the same class of "walking a collection whose element type
doesn't match the class's assumed API surface" as issue #276, but
considerably wider -- a full redesign of `OverlayOperations`'s
ownership model and base-class fit, not a one-line fix.
