# Live verification -- GitHub issue #246 (Duplicate() signature harmonisation)

**Project:** Sena 3 (restored fresh via `python scripts/restore_sena3.py`)
**Commits under test:** cc454c0 (production signatures + tests), 4c496c2 (.pyi stubs)
**Date:** 2026-08-18

## Commands

```
python scripts/restore_sena3.py
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest flexicon/sync/tests/test_duplicate_operations.py -m requires_live_project -q
```

Plus a throwaway equivalence script (not committed, run from scratchpad) that
opens Sena 3 directly via `FLExProject.OpenProject("Sena 3", writeEnabled=True)`,
duplicates the same source object both ways for the newly-added inert kwarg,
and re-queries the LCM by HVO via `project.Object(hvo)` cast to the concrete
interface before reading properties back.

## run_mode

`test_duplicate_operations.py` bypasses `tests/conftest.py` entirely (it calls
`FLExInitialize()` / `FLExProject().OpenProject("Sena 3", writeEnabled=True)`
directly in `setUpModule()`, per its own module docstring); there is no mock
fallback path in this file -- if SIL.LCModel/FieldWorks were unavailable it
would crash with a Windows access violation rather than silently degrade.
`tests/live_status.json` (written by the top-level conftest machinery) was
untouched by this run for that reason and still reflects an earlier, unrelated
session (`run_mode: live`, timestamps from a different test file). No
`[WARN] MOCK MODE` string appeared anywhere in this run's output, and every
Duplicate()/Delete() went through real `ILexEntryRepository`/`ServiceLocator`
lookups against `C:\ProgramData\SIL\FieldWorks\Projects\Sena 3\Sena 3.fwdata`.
Treated as live for this run.

## Claim under test

Every `Duplicate()` across 17 Operations classes now accepts both `deep=` and
`insert_after=` with no behaviour change where the kwarg is real, and no
`TypeError` where the kwarg is newly-added-and-inert.

## pytest result (point 1: no TypeError regression)

```
112 passed, 16 skipped, 58 warnings in 7.41s
```

0 failures. Includes all 7 previously-broken classes: AllomorphOperations,
EtymologyOperations, NaturalClassOperations, WfiGlossOperations,
WfiMorphBundleOperations (deep=), LexEntryOperations, TextOperations
(insert_after=). Also exercises deep/shallow-distinction tests for
LexSenseOperations, ParagraphOperations, ExampleOperations (point 3) --
all passed, no regression in real deep/shallow behaviour.

## Point 2: inert-kwarg equivalence (re-queried from LCM)

| Class | Kwarg | Source value | True-arg reread (hvo) | False-arg reread (hvo) |
|---|---|---|---|---|
| Allomorphs  | deep         | `rekerer` | `rekerer` (hvo=152448) | `rekerer` (hvo=152449) |
| Etymology   | deep         | `Sena`    | `Sena` (hvo=152450)    | `Sena` (hvo=152451)    |
| LexEntry    | insert_after | `cibubu`  | `cibubu` (hvo=152452)  | `cibubu` (hvo=152456)  |

All three re-reads used `project.Object(hvo)` (a fresh LCM `ServiceLocator`
lookup by HVO, not the Python object returned by `Duplicate()`), cast to the
concrete interface (`IMoForm` / `ILexEtymology` / `ILexEntry`), then read
via the class's own `GetForm`/`GetSource`/`GetLexemeForm`. Both True and
False arms matched the source value in all three cases.

Script output:
```
ALLOMORPH src form           : 'rekerer'
ALLOMORPH deep=True  reread  : 'rekerer' hvo= 152448
ALLOMORPH deep=False reread  : 'rekerer' hvo= 152449
ETYMOLOGY src source          : 'Sena'
ETYMOLOGY deep=True  reread   : 'Sena' hvo= 152450
ETYMOLOGY deep=False reread   : 'Sena' hvo= 152451
LEXENTRY src lexeme form            : 'cibubu'
LEXENTRY insert_after=True  reread  : 'cibubu' hvo= 152452
LEXENTRY insert_after=False reread  : 'cibubu' hvo= 152456
RESULT: ALL EQUIVALENCE CHECKS PASSED
```

## Cleanup

All 6 duplicates created by the equivalence script were deleted in the
script's `finally:` block:
```
cleaned up LexEntry 152456
cleaned up LexEntry 152452
cleaned up Etymology 152451
cleaned up Etymology 152450
cleaned up Allomorphs 152449
cleaned up Allomorphs 152448
```
The pytest suite's own tearDown/finally blocks cleaned up its own
duplicates. Post-run scan of Sena 3 for any `TEST_`-prefixed
`LexEntry.CitationForm` found 0 leftover entries. Database confirmed back
to pre-state.

## Result

[PASS] -- No TypeError from any Duplicate() call (112/112 pytest). Newly-added
`deep=`/`insert_after=` kwargs confirmed inert by direct LCM re-query on
3 representative classes. Real deep/shallow distinction on LexSense/
Paragraph/Example unaffected (all pytest cases passed).
