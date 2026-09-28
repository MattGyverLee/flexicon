# Issue #339 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/339-public-imports from origin/main

## RULING (binding)

Runtime logs showed `ImportError: cannot import name 'MSAOperations'` and
`PhonFeatureOperations` from `flexicon` after callers guessed class names from
incomplete discovery (#257, FlexToolsMCP#100). Issue #257's fix landed in
#311 (`__init__.py` / stub parity); #339 tracks **regression prevention** for
those two high-traffic names.

**Correct behaviour (issue #339 scope):**

1. **`MSAOperations` and `PhonFeatureOperations`** must remain eager imports
   in `flexicon/__init__.py` and entries in runtime `__all__`.
2. **`flexicon/__init__.pyi`** must declare the same names in stub `__all__`
   (enforced by the existing #297 parity ratchet; this issue adds an explicit
   #339 pin so log-scan failures cannot slip past a narrow stub edit).
3. **Out of scope:** FlexToolsMCP discovery/index fixes (#100), renaming
   `PhonFeatureOperations` to match user guesses, or exporting additional
   facade-only classes beyond the #257 set.

## Verification plan

- Offline: `tests/test_issue339_public_import_surface.py` (AST-only, no `clr`).
- Live: not required (import surface only; no LCM write path).
