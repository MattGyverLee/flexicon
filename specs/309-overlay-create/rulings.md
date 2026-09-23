# Issue #309 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/309-overlay-create from origin/main

## RULING (binding)

Issue #309's suggested chart-scoped `Create(chart, name)` is **rejected**. Live
reflection (issue #303, `specs/lcm-member-truth-sweep/reviews/cycle1-domain.md`)
confirms overlays are **project-scoped** at `ILangProject.OverlaysOC`; `IDsConstChart`
has no overlay members.

**Correct behaviour for this PR (scoped to #309 -- Create path + minimal CRUD
supporting it):**

1. **Create(name, poss_list, items=None)** -- `ICmOverlayFactory.Create()`,
   `lp.OverlaysOC.Add(overlay)`, assign `overlay.Name` as a plain string (no
   `wsHandle`; `ICmOverlay.Name` is `System.String`), require non-null `poss_list`
   for `PossListRA`, optionally seed `PossItemsRC` from `items`.
2. **GetAll()** -- `list(lp.OverlaysOC)`.
3. **GetName / SetName / Find / Exists / Delete** -- reimplemented on this class
   for plain-string `Name` and `OverlaysOC` membership (inherited
   `PossibilityItemOperations` paths use `PossibilitiesOS` / `IMultiString` and
   remain wrong for `ICmOverlay`).

**Out of scope (issue #303 / lcm-member-truth-sweep):** re-base on
`BaseOperations`, delete chart-scoped helpers, visibility/display-order,
description, duplicate, full sync rewrite.

## Verification plan

- Offline: source ratchet + unit tests for Create/GetAll/Find/GetName.
- Live: extend `tests/operations/test_overlay_operations.py` with
  `project.Overlays.Create(...)` round-trip on `sena3_sandbox` when
  `FLEXLIBS_REQUIRE_LIVE=1`.
