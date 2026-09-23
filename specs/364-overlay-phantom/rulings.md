# Issue #364 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/364-overlay-phantom-guards from origin/main

## RULING (binding)

Live reflection for #277/#303/#320 confirms `ICmOverlay` exposes only
`Name`, `PossItemsRC`, and `PossListRA`. There is no `IsVisibleRA`,
`Hidden`, `ChartRA`, or `Chart` on that surface.

**Correct behaviour (issue #364 scope):**

1. **IsVisible / SetVisible** -- Drop the `IsVisibleRA` branches entirely.
   Do not treat `Hidden` as an overlay visibility field (it is not on
   `ICmOverlay`). `IsVisible` returns `True` when no visibility member
   exists; `SetVisible` logs at debug and returns without opening a
   transaction (no LCM field to write).
2. **GetChart** -- Drop the `ChartRA` / `Chart` fast paths; always use the
   existing `OwnerOfClass(DsConstChartTags.kClassId)` walk. For
   project-scoped overlays this continues to return `None` (#303).

**Out of scope:** Retiring chart-scoped helpers (#303), display order, or
re-basing off `PossibilityItemOperations`.

## Verification plan

- Offline: source ratchets on `IsVisible`, `SetVisible`, and `GetChart`;
  update Pattern G mirror test for GetChart.
- Live: optional -- no write path; existing overlay live tests unchanged.
