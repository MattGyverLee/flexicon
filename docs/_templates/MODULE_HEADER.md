# Template: Python Module Header

Use this when creating a new Python source file under `flexicon/code/`. Place at the very top, before imports.

## Format

```python
#
#   <ModuleName>.py
#
#   Class: <ClassName>
#          <One-line description of the class's responsibility>.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright <year>
#
```

## Worked examples

### Operations class

```python
#
#   LexEntryOperations.py
#
#   Class: LexEntryOperations
#          Lexical entry operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#
```

### Shared utility module (no single class)

```python
#
#   string_utils.py
#
#   Module: Shared string-handling utilities for FLEx multilingual fields.
#           Includes FLEX null marker handling ('***' -> ''), NFD/NFC
#           normalization, and best-analysis text resolution.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#
```

### Test module

```python
#
#   test_lexsense_single_string_fields.py
#
#   Class: TestLexSenseSingleStringFields
#          Regression coverage for ITsString single-string fields on
#          ILexSense (Source / ScientificName / ImportResidue).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#
```

## Rules

- **Match the module's content type.** Operations classes get `Class: <name>`. Utility modules get `Module:` instead.
- **Two-line description.** First line tags the role; second line scopes it concretely.
- **Copyright year:** match the rest of the codebase (not the year the file was added). The standard is `Copyright 2025` for current source. Bump in coordinated passes, not per-file.
- **No emojis. No issue numbers.** Per project CLAUDE.md.
- **No author lines, no version metadata in the header.** Git provides that.
- **Always blank line between header and the first `import`.**

## When NOT to use this template

- Auto-generated files (Sphinx output, etc.)
- Third-party vendored code (preserve upstream header)
- One-off scripts under `scripts/` — use a lighter `#  scripts/<name>.py  —  <one-line purpose>` instead
