# Issue #303 -- lex-lead ruling (inherited surface remainder)

**Date:** 2026-09-23  
**Branch:** fix/303-overlay-inherited-surface from origin/main

## Context

PR #372 / issue #309 fixed Create, GetAll, Delete, Find, Exists, GetName, and
SetName. Issue #303 still lists inherited possibility-shaped methods that crash
or no-op on real `ICmOverlay` objects, plus chart-scoped helpers that read
phantom chart members.

## RULING (binding)

**Scope:** Remaining inherited / wrong-premise **read and duplicate** paths on
`OverlayOperations`. Do not re-base the class off `BaseOperations` in this PR.

1. **Duplicate** -- Implement on `OverlayOperations`: `ICmOverlayFactory.Create()`,
   `OverlaysOC.Add`, copy plain `Name`, `PossListRA`, and `PossItemsRC` entries
   from source. `insert_after` is ignored (unordered OC).
2. **GetDescription / SetDescription** -- `ICmOverlay` has no `Description`.
   `GetDescription` returns `""`; `SetDescription` is a validated no-op.
3. **CompareTo** -- Compare plain `Name` strings (case-sensitive ordinal), not
   `IMultiString.get_String`.
4. **GetSyncableProperties** -- Emit `Guid`, plain-string `Name`, and when set
   `PossListRA` as GUID string. Do not read `Description`.
5. **FindByChart / GetVisibleOverlays** -- Overlays are project-scoped (#303).
   `FindByChart(chart)` returns `GetAll()` (chart argument validated only;
   documented as ignored for lookup). `GetVisibleOverlays(chart)` filters that
   list with `IsVisible` (chart argument validated only).

**Out of scope:** Display order, element CRUD beyond existing guards, retiring
`PossibilityItemOperations` inheritance, full sync rewrite.

## Verification plan

- Offline: extend `tests/operations/test_overlay_operations.py` source ratchets.
- Live: optional read-only `GetSyncableProperties` / `CompareTo` on existing
  overlays when LCM available.
