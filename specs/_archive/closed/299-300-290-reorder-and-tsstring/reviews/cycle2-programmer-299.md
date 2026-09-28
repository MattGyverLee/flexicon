# Programmer Report — Issue #299 `_GetSequence` fixes (cycle 2)

**Date:** 2026-09-10
**Status:** DONE — implemented exactly per `cycle1-domain.md` ruling (contradicts the
GitHub issue's own proposed fix, as instructed).

## Changes made

1. **`flexicon/code/TextsWords/TextOperations.py`** — DELETED the `_GetSequence`
   override (was `return parent.ContentsOS`, docstring "for text paragraphs").
   No replacement. `TextOperations` now falls through to
   `BaseOperations._GetSequence`'s `NotImplementedError`, matching the existing
   `LexEntryOperations` precedent (no override there either). Rationale:
   `project.lp.Texts` is an owning **collection** (`TextsOC`), not a sequence —
   no indexer, no `.MoveTo()`.

2. **`flexicon/code/TextsWords/ParagraphOperations.py`** — `_GetSequence` now
   returns `parent.ContentsOA.ParagraphsOS` (parent = `IText`, matching
   `Create`/`GetAll`/`InsertAt`'s `__GetTextObject` contract). Previously wrongly
   returned `parent.SegmentsOS` (a paragraph's segments, not a text's
   paragraphs — copied verbatim from the domain report).

3. **`flexicon/code/TextsWords/SegmentOperations.py`** — `_GetSequence` now
   returns `parent.SegmentsOS` (parent = `IStTxtPara`, matching `GetAll`/
   `AppendSentence`'s `__GetParagraphObject` contract). Previously wrongly
   returned `parent.AnalysesRS`. Docstring corrected from "segment analyses
   (reference sequence)" to explain `AnalysesRS` is out of scope (issue #215
   already owns it via `SetAnalysis`/`ReplaceAnalysis`/`InsertAnalysis`/
   `AppendAnalysis`/`RemoveAnalysis`) — copied verbatim from the domain report.

All three docstrings match the domain report's "Exact code for the
implementer" section verbatim.

## Mandatory regression sweep

Grepped the entire repo (`tests\`, `examples\`, `demos\`, `docs\`, `flexicon\`,
plus specs/changelogs) for:
- `Texts.Sort|MoveUp|MoveDown|MoveToIndex` / `project.Texts.Sort()` etc.
- `TextOperations._GetSequence` direct references
- `Paragraphs.Sort|MoveUp|MoveDown|MoveToIndex`
- `Segments.Sort|MoveUp|MoveDown|MoveToIndex`

**Result: zero hits anywhere in code, tests, examples, or docs.** No caller in
the repo invokes reorder methods on `project.Texts`, `project.Paragraphs`, or
`project.Segments`, and nothing references `TextOperations._GetSequence`
directly. No existing test asserted the old (broken) behavior, so nothing
needed updating. `docs\FUNCTION_REFERENCE.md` and
`docs\operations\TEXTOPERATIONS_USAGE.md` reference `project.Texts.Create/
Delete/GetAll/...` but never Sort/MoveUp/MoveDown/MoveToIndex, so no doc
changes were required.

## New tests

Added `tests/operations/test_299_getsequence_ownership_fix.py`, mock-only,
following `test_300_getsequence_property_rename.py`'s structure (deliberately
shape mocks to expose only the correct attribute so a regression to the old
target raises `AttributeError` rather than silently passing):

- `TestParagraphOperationsGetSequence` — pins `parent.ContentsOA.ParagraphsOS`
  off an `IText`-shaped mock; guards mock has no `SegmentsOS`; falsifier
  confirms the old target raises `AttributeError`.
- `TestSegmentOperationsGetSequence` — pins `parent.SegmentsOS` off an
  `IStTxtPara`-shaped mock; guards mock has no `AnalysesRS`; falsifier
  confirms the old target raises `AttributeError`.
- `TestTextOperationsGetSequenceRemoved` — asserts `_GetSequence` is absent
  from `TextOperations.__dict__` and resolves to the inherited
  `BaseOperations._GetSequence`; asserts `Sort()` and `MoveUp()` both raise
  `NotImplementedError` (via a minimal write-enabled mock project, since
  `MoveUp` calls `_EnsureWriteEnabled()` before `_GetSequence`).

None marked `requires_live_project`.

## Test run

```
python -m pytest tests/operations/test_299_getsequence_ownership_fix.py tests/operations/test_300_getsequence_property_rename.py -q
15 passed in 1.31s
```

No bare `pytest` or live tests were run this cycle.

## Scope discipline

Did not touch, revert, or stage the pre-existing uncommitted #300 work in
`WfiMorphBundleOperations.py` or `DataNotebookOperations.py` (confirmed still
present and untouched via `git status`). Also left `ConstChartRowOperations.py`
(pre-existing unrelated modification, not part of this task) untouched. All
changes remain unstaged in the working tree; nothing was committed.
