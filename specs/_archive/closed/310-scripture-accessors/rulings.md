# Issue #310 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/310-scripture-accessors from origin/main

## RULING (binding)

Six Scripture Operations classes exist; docstrings and integration tests
assume `project.ScrBooks`, `project.ScrDrafts`, `project.ScrNotes`,
`project.ScrSections`, `project.ScrTxtParas`, and `project.ScrAnnotations`.
Only `ScrBooks` and `ScrDrafts` were wired on `FLExProject` when this issue
was filed.

**Correct behaviour (issue #310 scope):**

1. Add cached `@property` accessors on `FLExProject` for the four missing
   Operations classes, matching the lazy-import + `_scr*_ops` cache pattern
   used by `ScrBooks` and `ScrDrafts`.
2. Declare the same accessors on `FLExProject.pyi` so docstring-example
   ratchets resolve accessor types.
3. Shrink `tests/docstring_example_baseline.json` for findings that no
   longer reproduce once accessors exist.

**Out of scope:** Changing Scripture Operations method behaviour, MCP index
updates, or live write-path verification (accessors only; no LCM writes).

## Verification plan

- Offline: structural test that all six accessors exist as properties and
  return the expected Operations class on a mock project; docstring ratchet
  baseline shrink; `python -m pytest -m "not requires_live_project" -q`.
- Live: optional read-only open project and touch each accessor when LCM is
  available (no write path).
