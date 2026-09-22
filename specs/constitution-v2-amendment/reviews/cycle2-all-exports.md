# Cycle 2 -- `__all__` for flexicon/__init__.py

## Method

Parsed `flexicon/__init__.py` with `ast` (no package import relied upon for
derivation). Collected every module-level binding: `from X import (...)`
targets (with `as`-aliases), plain `import x` targets, and module-level
`Assign`/`AnnAssign` targets (`version`, `CAPABILITIES`). Total bound names:
99. Set P = names not starting with `_`: **|P| = 99** (every binding in the
file is already public by convention -- there are zero leading-underscore
names to exclude).

## Count by kind

- Constants: 9 -- `version`, `CAPABILITIES`, `FWCodeDir`, `FWProjectsDir`,
  `FWExecutable`, `FWShortVersion`, `FWLongVersion`, `APIHelpFile`,
  `FLEX_NULL_MARKER` (the six `FW*`/`APIHelpFile` names are module-level
  `None`/path assignments in `FLExGlobals.py`, not functions -- confirmed
  by grep, not import).
- Functions: 13 -- `FLExInitialize`, `FLExCleanup`, `AllProjectNames`,
  `OpenProjectInFW`, `normalize_text`, `is_empty_text`,
  `best_analysis_text`, `best_vernacular_text`, `best_text`, `wrap`,
  `unwrap`, `p`, `cast_to_concrete`.
- Exceptions: 11 -- `FP_ConflictingSaveError`, `FP_FileLockedError`,
  `FP_FileNotFoundError`, `FP_MigrationRequired`, `FP_NullParameterError`,
  `FP_ParameterError`, `FP_ProjectError`, `FP_ReadOnlyError`,
  `FP_RuntimeError`, `FP_TransactionError`, `FP_WritingSystemError`.
- Classes (incl. enum-like/wrapper types): 66 -- `FLExProject`,
  `HeadlessLcmUI`, `PythonicWrapper`, all ~55 `*Operations` classes across
  Grammar/Lexicon/TextsWords/Notebook/Lists/System/Reversal/Discourse/Parser,
  plus `SpellingStatusStates`, `ApprovalStatusTypes`, `MediaType`, `Seg`,
  `NC`, `Boundary`.
- Modules: 0 -- no bare `import x` submodule bindings exist at module level
  in this file.

Full list (99 names, alphabetical) is what was written into `__all__`; see
the file itself -- omitted here only for length, though it is under the
120-name cap, since it is a mechanical duplicate of the code.

## Candidates for a future gated removal

None. Every one of the 99 names is a deliberate, documented export (several
carry explicit comments citing the issues that added them, e.g. #257,
#271, #285). No stray `import logging`-style leakage or incidental
submodule binding was found. `__all__` was set to the full 99, matching P
exactly -- no narrowing.

## Package import check

Attempted `python -c "import flexicon"` as a diagnostic only (not relied
upon for the `__all__` derivation, per instructions). It **succeeded** in
this environment: `import OK`, `len(flexicon.__all__) == 99`. Likely
because FieldWorks/pythonnet dependencies are lazily deferred rather than
touched at import time (consistent with the in-file comments about
`ParserOperations` and `lcm_casting` deferring their heavy imports).

## Verification

Re-parsed the edited file: `__all__` has 99 entries, sorted, no duplicates,
matching the computed P exactly.
