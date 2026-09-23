# Issue #303 -- lex-lead close-out ruling

**Date:** 2026-09-23  
**Branch:** fix/303-overlay-closeout-v6 from origin/main

## Context

PRs #309, #372, #384, and #378 landed the functional fixes for project-scoped
``OverlaysOC``, plain-string ``Name``, and ``ICmOverlay``-specific CRUD/sync.
Issue #303 remained open because the GitHub issues were referenced, not closed,
and inherited **reorder** methods still inherited from ``PossibilityItemOperations``
without an honest failure mode.

## RULING (binding)

1. **Close issue #303** once this PR merges. Remaining architectural question
   (whether to stop inheriting ``PossibilityItemOperations`` entirely) stays a
   follow-up design item, not a blocker: every path named in the issue body is
   now either overridden or raises ``NotImplementedError`` at ``_GetSequence``.
2. **`_GetSequence`** -- Raise ``NotImplementedError`` with an explicit message
   that ``ILangProject.OverlaysOC`` is an unordered ``ILcmOwningCollection``
   (same precedent as issue #301 / ``ConstChartMarkerOperations``).
3. **Docstrings** -- Correct chart-scoped wording on ``FindByChart`` /
   ``GetVisibleOverlays`` and the class CRUD list; overlays are project-scoped.

## Verification plan

- Offline: extend ``tests/operations/test_overlay_operations.py`` source ratchets;
  run ``python -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q``.
- Live: optional; no new write path.
