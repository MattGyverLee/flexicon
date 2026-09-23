# Issue #303 -- close-out (offline evidence)

## Lex-lead ruling

`specs/303-overlay-closeout/rulings.md`

## Commands

```
python3 -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

7 passed, 4 deselected.

## Behaviour

| Remainder | Change |
|-----------|--------|
| Inherited `Sort` / `MoveUp` / … on overlays | `_GetSequence` raises `NotImplementedError` (unordered `OverlaysOC`) |
| Stale chart-scoped docstrings | Updated to project-scoped `#303` wording |

Prior tranches (#309 Create/GetAll, #384 inherited surface, #364 phantom guards)
unchanged; verified by existing ratchets in the same test module.

**Live:** FAIL: unverified on cloud agent (no FieldWorks / `clr`).
