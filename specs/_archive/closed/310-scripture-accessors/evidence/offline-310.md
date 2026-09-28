# Issue #310 -- Scripture FLExProject accessors (offline evidence)

## Lex-lead ruling

See `specs/310-scripture-accessors/rulings.md`.

## Commands

```
python -m pytest tests/test_issue310_scripture_accessors.py tests/test_docstring_example_ratchet.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux)

**FAIL: unverified** -- pytest is not installed on this cloud host and pythonnet
requires FieldWorks for import-heavy paths. Structural change reviewed in-tree:
four accessors added, pyi updated, baseline shrunk by 80 entries.

## Pre/post behaviour

| Accessor | Before | After |
|----------|--------|-------|
| ScrBooks | present | unchanged |
| ScrDrafts | present | unchanged |
| ScrNotes | missing | lazy property -> ScrNoteOperations |
| ScrSections | missing | lazy property -> ScrSectionOperations |
| ScrTxtParas | missing | lazy property -> ScrTxtParaOperations |
| ScrAnnotations | missing | lazy property -> ScrAnnotationsOperations |

**Pass/fail:** code complete; machine gate not run on this agent.
