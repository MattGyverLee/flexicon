# Cycle 1 -- Programmer report: issue #300

## Summary

Fixed both `_GetSequence` overrides identified in issue #300. Both were
one-line property renames plus a docstring correction naming the real
property and parent type. No other `_GetSequence` override was touched
(issue #299's TextOperations/ParagraphOperations/SegmentOperations sites
are out of scope this cycle and were left untouched). No live LCM tests
were run this cycle per instructions; only mock/offline coverage was
added.

## Files changed

### `flexicon\code\TextsWords\WfiMorphBundleOperations.py`
- Lines 91-97 (was 91-93): `_GetSequence` now returns
  `parent.MorphBundlesOS` instead of the nonexistent `parent.MorphsOS`.
  Docstring expanded to state the parent is `IWfiAnalysis` and that
  `MorphsOS` does not exist on it.

### `flexicon\code\Notebook\DataNotebookOperations.py`
- Lines 125-131 (was 125-127): `_GetSequence` now returns
  `parent.SubRecordsOS` instead of the nonexistent `parent.RecordsOS`.
  Docstring expanded to state the parent is `IRnGenericRec` and that
  `RecordsOS` does not exist on it.

## New test file

`tests\operations\test_300_getsequence_property_rename.py`

Mock-only regression coverage (no live project, `pytest.mark.requires_live_project`
not applied):

- `TestWfiMorphBundleGetSequenceProperty` -- mock `IWfiAnalysis` stand-in
  exposes only `MorphBundlesOS` (no `MorphsOS`). Pins that
  `WfiMorphBundleOperations._GetSequence` returns the real sequence
  object, asserts the mock has no `MorphsOS` attribute (guards the test
  itself against a false pass), and asserts reading the old attribute
  name raises `AttributeError` (the documented pre-fix failure mode).
- `TestDataNotebookGetSequenceProperty` -- same structure for
  `DataNotebookOperations._GetSequence` against a mock `IRnGenericRec`
  exposing only `SubRecordsOS` (no `RecordsOS`).

Each class has 3 tests (6 total): the positive regression pin, a mock-shape
guard, and a direct `AttributeError` falsifier for the old property name.

## Offline test result

```
python -m pytest tests/operations/test_300_getsequence_property_rename.py -q
......                                                                   [100%]
6 passed in 1.25s
```

Run targeted only, per instructions -- no bare `pytest` invocation.

## Not done this cycle (by design)

- No live LCM verification (another agent holds the live session).
  Scheduled for cycle 2 per the task briefing.
- No changes to TextOperations, ParagraphOperations, or SegmentOperations
  (issue #299, handled separately).
- No commit -- changes left in the working tree per instructions.
