# Issue #314 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/314-default-ws-properties from origin/main

## RULING (binding)

The orphaned `core/types.py` `FlexProject` protocol promises two int-returning
properties: `DefaultVernacularWs` and `DefaultAnalysisWs`. `FLExProject` must
implement them as **thin aliases** of the existing handle helpers -- no new LCM
access paths.

**Correct behaviour:**

1. `DefaultVernacularWs` -> `GetDefaultVernacularWSHandle()` (same int).
2. `DefaultAnalysisWs` -> `GetDefaultAnalysisWSHandle()` (same int).
3. Docstrings on the tuple-returning `GetDefault*WS()` methods must cross-link
   to the property and `*WSHandle()` sibling so callers stop guessing names.
4. Mark `FlexProject` `@runtime_checkable` and add an offline structural test
   that `FLExProject` satisfies the protocol (attribute presence + property kind).

**Out of scope:**

- Renaming or removing `GetDefault*WSHandle()` (keep both spellings).
- Changing tuple-returning `GetDefault*WS()` semantics.
- MCP index updates (separate FlexToolsMCP work).

## Verification plan

- Offline: protocol ratchet + `dir()` discoverability for the two properties;
  mock delegation test (no LCM).
- Live: extend `tests/test_flexproject_discoverability.py` to assert properties
  match `*WSHandle()` on an open project when FieldWorks is available.
