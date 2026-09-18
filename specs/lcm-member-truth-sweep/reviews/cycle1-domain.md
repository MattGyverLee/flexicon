# Domain Expert Ruling: OverlayOperations rewrite

**Campaign:** lcm-member-truth-sweep, cycle 1
**Issues:** #303 (root), #309 (symptom)
**Date:** 2026-09-18
**Status:** RULING DELIVERED

> Provenance note: produced by the `lex-domain` subagent, which has no
> Write/Edit tools in its agent definition. Persisted to this path verbatim
> by the main session on its behalf. Content is unmodified.

## 1. Inheritance: drop PossibilityItemOperations, inherit BaseOperations directly

`ICmOverlay`'s complete own-declared surface (live-confirmed) is `Name`
(plain `System.String`), `PossItemsRC`, `PossListRA` -- nothing else, and
`ICmPossibility.IsAssignableFrom(ICmOverlay)` is `False`. Walking
`possibility_item_base.py`'s contract against that surface: of the 13
methods a subclass inherits unmodified (`GetAll, Create, Delete,
Duplicate, Find, Exists, GetName, SetName, GetDescription,
SetDescription, GetGuid, CompareTo, GetSyncableProperties`), **12 touch
either `list_obj.PossibilitiesOS`** (no such `CmPossibilityList` backs
an overlay -- `_get_list_object()` correctly returns `None`) **or
`item.Name.get_String(...)`/`item.Description...`** (Name isn't
multilingual; Description doesn't exist at all). Only `GetGuid` (`str
(item.Guid)`, universal on `ICmObject`) would work as-is.

Compare the repo's own working precedent, `AgentOperations`: it also
inherits `PossibilityItemOperations` for a type that lives in a plain
`ILcmOwningCollection` (`AnalyzingAgentsOC`), but it only had to override
5 methods (`GetAll/Create/Delete/Duplicate/Find`) because `ICmAgent.Name`
*is* `ITsString`-compatible -- `GetName/SetName/GetDescription/
SetDescription/GetGuid/CompareTo` were left inherited and work. Overlay
fails that same test: `Name` is plain string, `Description` doesn't
exist, so the AgentOperations-style "override just the OC-shaped CRUD"
pattern doesn't transfer -- Overlay needs *all 12* rewritten anyway.

`PossItemsRC`/`PossListRA` confirm the deeper point: an overlay
*references* possibilities (a saved selector over some other list via
`PossListRA`, with `PossItemsRC` the selected subset) -- it is not itself
a possibility and is not an item *in* a list. Inheriting a class named
`PossibilityItemOperations`, reusing ~1 of 13 methods unmodified, for a
type that fails the base class's own "is a possibility item in a
possibility list" premise at both the type level and the object level,
is categorically wrong, not merely suboptimal. **Rule: inherit
`BaseOperations` directly.**

## 2. Scoping: re-root on `ILangProject.OverlaysOC`

- `GetAll()` -> `list(self.project.lp.OverlaysOC)`.
- `Create(name, poss_list, items=None)` -> `ICmOverlayFactory.Create()`,
  `lp.OverlaysOC.Add(overlay)`, `overlay.Name = name` (direct string
  assignment -- no wsHandle; there is no per-WS value to select), require
  a non-null `poss_list` for `PossListRA` (an overlay with no source
  list is a selector over nothing -- should raise `FP_ParameterError` if
  omitted, not silently create a dangling overlay), optionally seed
  `PossItemsRC`.
- `Delete(overlay_or_hvo)` -> resolve, `lp.OverlaysOC.Remove(overlay)`
  inside `_TransactionCM`, same shape as the base's `Delete` but against
  `OC` not `PossibilitiesOS`.
- `Find(name)` -> iterate `GetAll()`, compare `overlay.Name` via
  `normalize_match_key` directly (no `wsHandle` parameter at all in the
  rewritten `GetName`/`SetName` signatures -- passing one would be
  nonsensical against a field that is not multilingual; this is a
  signature difference forced by the LCM type, not a caller-facing flag,
  so CLAUDE.md's anti-flag rule doesn't bear on it directly, but the
  same spirit applies: don't paper over the type mismatch with an
  ignored parameter).
- `GetChart()`/`FindByChart()`: **delete outright**, don't keep as an
  error-raising stub. These aren't "broken until you opt in to a fix" --
  live reflection proves `IDsConstChart` has zero overlay-related
  members and `ICmOverlay` has zero chart-reference members, so the
  premise is false for 100% of inputs, permanently. A raising stub adds
  no value; nothing currently depends on working behaviour here (both
  already silently returned `[]`/`None`). The repo's own precedent
  (Category 10, `SegmentOperations.Create`/`.Duplicate` removal) is
  straight deletion plus a migration table in
  `docs/API_ISSUES_CATEGORIZED.md`, not a shim -- follow that exactly.

## 3. Method triage

| Method | Verdict | Notes / replacement |
|---|---|---|
| `GetAll` | REWRITE | `list(lp.OverlaysOC)` |
| `Create` | REWRITE | factory + `OC.Add` + plain-string `Name` + required `PossListRA` |
| `Delete` | REWRITE | `OC.Remove` |
| `Duplicate` | REWRITE | new overlay; `Name` = plain copy, not `CopyAlternatives` (not `IMultiString`); copy `PossListRA`/`PossItemsRC` |
| `Find` | REWRITE | plain-string compare, no wsHandle |
| `Exists` | REWRITE | trivial, must move onto subclass (no longer inherited) |
| `GetName` | REWRITE | `overlay.Name` direct read, drop wsHandle param |
| `SetName` | REWRITE | `overlay.Name = name` direct write, drop wsHandle param |
| `GetDescription` | DELETE | `ICmOverlay` has no `Description` field at all (not a type mismatch -- total absence). Caller: there is nothing to migrate to; overlays have no description concept. |
| `SetDescription` | DELETE | same |
| `GetGuid` | KEEP-AS-IS | universal `ICmObject.Guid` |
| `CompareTo` | REWRITE | plain-string compare, no wsHandle |
| `GetSyncableProperties` | REWRITE | drop per-WS alternatives loop; return flat `{Guid, Name}`, no `Description` key |
| `IsVisible` | DELETE | rests on `IsVisibleRA`/`Hidden`, neither exists (confirmed: complete 3-prop surface is `Name/PossItemsRC/PossListRA`). No replacement -- visibility isn't a modelled LCM concept for overlays. |
| `SetVisible` | DELETE | same |
| `GetDisplayOrder` | DELETE | `SortSpec` doesn't exist on `ICmOverlay` |
| `SetDisplayOrder` | DELETE | same |
| `GetElements` | DELETE | `InstancesOS`/`Elements` don't exist; conceptually a duplicate of `GetPossItems` (the real member set is `PossItemsRC`). Caller: use `GetPossItems`. |
| `AddElement` | DELETE | same; no `PossItemsRC` write method exists yet -- flag as a **recommended new method** (`AddPossItem`), out of scope to add silently here |
| `RemoveElement` | DELETE | same -> recommend `RemovePossItem` |
| `GetChart` | DELETE | premise categorically false (see section 2); no replacement exists because the scoping assumption itself was wrong |
| `GetPossItems` | KEEP-AS-IS | already live-fixed under #277, reads `PossItemsRC` correctly |
| `FindByChart` | DELETE | `chart.OverlaysOC` doesn't exist on `IDsConstChart`. Caller: use `GetAll()` (overlays are project-wide, not chart-scoped -- there is no true chart-filtered replacement because charts never owned overlays) |
| `GetVisibleOverlays` | DELETE | depends on deleted `FindByChart` + deleted `IsVisible`; no replacement, visibility isn't modelled |

**Public-surface check:** `OverlayOperations.pyi` only pins `GetAll,
Find, Exists, Create, Delete, Duplicate, GetName, SetName, GetGUID` (plus
a catch-all `__getattr__`). Every one of those is either KEEP-AS-IS or
REWRITE above -- **none of the 10 DELETE candidates are part of the
pinned type-stub contract.** `README.rst` mentions "Overlays" only at
the module-list level, no method-level API. This substantially derisks
the breaking change.

## 4. Breaking-change call: straight removal, no deprecation shim

All 10 DELETE-flagged methods are proven, by live LCM reflection, to be
unconditionally non-functional (empty/no-op/`AttributeError`) against a
real `ICmOverlay` today -- there is no working behaviour to preserve or
deprecate. None appear in the pinned `.pyi` surface. Repo precedent
(Category 10, `docs/API_ISSUES_CATEGORIZED.md:627-682`) for an
equivalent situation (`SegmentOperations.Create`/`Duplicate`) is
straight removal plus a migration table, not a raising stub or
deprecation cycle -- follow that shape exactly: new
`docs/API_ISSUES_CATEGORIZED.md` category entry with an
old-API/new-API table and a "why removed" note, updated class docstring
and usage example (the current one calls `Create()`, `SetDescription()`,
`SetVisible()`, `SetDisplayOrder()`, `FindByChart()`,
`GetVisibleOverlays()` -- all either rewritten or deleted), and a
`.pyi` update. Given the recent `4.8.0` "silent-failure sweep" pattern
on `main`, a normal release note under the existing versioning
discipline is sufficient; no major-version gate needed since nothing
functional is being taken away.

## 5. Spurt breakdown (recommend 3 spurts)

- **Spurt A -- re-scope + core CRUD rewrite.** Drop
  `PossibilityItemOperations` inheritance; implement
  `GetAll/Create/Delete/Duplicate/Find/Exists/GetName/SetName/GetGuid/
  CompareTo/GetSyncableProperties` against `ILangProject.OverlaysOC` +
  plain-string `Name`; keep `GetPossItems` untouched. Live-verify
  writes on `target_sandbox`, reads on `sena3_sandbox` (reuse the #277
  evidence file's fixtures/pre-existing overlay).
- **Spurt B -- deletions + PossListRA/PossItemsRC completion.** Delete
  the 10 dead methods; rewrite class docstring/usage example; optionally
  add `SetPossList`/`AddPossItem`/`RemovePossItem` to give
  `PossListRA`/`PossItemsRC` a real CRUD surface (currently read-only).
  Live-verify writes on `target_sandbox`.
- **Spurt C -- docs & tests.** Update `OverlayOperations.pyi`,
  `docs/API_ISSUES_CATEGORIZED.md` (new Category-10-style entry),
  rewrite `tests/operations/test_overlay_operations.py` for the new
  shape, refresh ratchet / `tests/live_status.json` coverage.

Relevant files read: `specs/277-nonexistent-property-reads/evidence/live-277-overlays.md`, `flexicon/code/Lists/OverlayOperations.py`, `flexicon/code/Lists/possibility_item_base.py`, `flexicon/code/Lists/AgentOperations.py`, `flexicon/code/Lists/OverlayOperations.pyi`, `docs/API_ISSUES_CATEGORIZED.md` (Category 8, Category 10), `README.rst`.
