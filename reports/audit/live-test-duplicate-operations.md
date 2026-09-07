# Live verification evidence: `test_duplicate_operations.py`

## Placement note

Per CLAUDE.md's Live LCM Verification section, this evidence file would
normally live at `specs/<feature>/evidence/live-<task>.md`. The task that
produced it explicitly forbids touching anything under `specs/` (concurrent
4.4.0 release cut in that directory), so it is placed here instead:
`reports/audit/live-test-duplicate-operations.md`. See the same note in
`reports/audit/duplicate-signature-audit.md`.

## Command (run identically before every measured pass)

```
python scripts/restore_sena3.py
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest flexicon/sync/tests/test_duplicate_operations.py -m requires_live_project -q -p no:cacheprovider --tb=short
```

## `run_mode`

`tests/live_status.json` -> `"run_mode": "live"` (confirmed after the final
green run; file mtime matches the run). No `[WARN] MOCK MODE` string appears
anywhere in any captured run's stdout/stderr across the 5 iterations below --
also independently confirms live mode, since 112 real passing assertions
(headwords, GUIDs, sense/segment counts, etc.) are only satisfiable against
the real Sena 3 LCM data, not a mock.

## Before / after

| Run | Restored Sena 3 first? | Result |
|---|---|---|
| Baseline (given) | Yes | 69 failed, 27 passed, 16 skipped, 16 errors |
| After Shape-1 casting fixes + Shape-2 test signature fixes | Yes | 3 failed, 8 errors, 104 passed, 16 skipped |
| After LexEntry/Paragraph/Note fixes (round 2) | Yes | 8 failed (all Note), 104 passed, 16 skipped |
| After NoteOperations Source->SourceRA + LangProject casting fix | Yes | 8 failed (Note Delete NullReferenceException), 104 passed, 16 skipped |
| **Final**, after NoteOperations.Delete double-delete guard | Yes | **112 passed, 16 skipped, 0 failed, 0 errors** |

## Pre-state / post-state read-back samples (not just "didn't crash")

- **LexEntry headword/lexeme form**: `GetLexemeForm(source)` read before
  `Duplicate()`, then `GetLexemeForm(duplicate)` read back afterward and
  compared equal (`test_duplicate_copies_properties`). Confirms the copy
  landed in the LCM store, not just that the call returned.
- **LexEntry shallow duplicate sense count**: after fixing
  `create_blank_sense=False`, read back `duplicate.SensesOS.Count` and
  asserted `== 0` (was `== 1` before the fix, i.e. this specifically
  re-queries the LCM collection post-write, not the value passed in).
- **Note round-trip**: created a real `TEST_`-prefixed `ICmBaseAnnotation` via
  `project.Notes.Create()`, duplicated it, read back
  `str(duplicate.Guid) != str(original.Guid)`, then deleted the duplicate and
  confirmed no exception (previously threw
  `System.NullReferenceException` at `CmObject.ICmObjectInternal.DeleteObject()`
  on the double-delete).
- **Paragraph deep-copy segments**: read back `duplicate.SegmentsOS.Count`
  after `Duplicate(deep=True)` and asserted `> 0` (previously asserted an
  exact count match against re-parsed/re-segmented output, which the
  method's own docstring does not promise).

## Pass/fail line (final)

```
112 passed, 16 skipped, 59 warnings in 6.03s
```

`FAILED`/`ERROR`: none. The 16 skipped are pre-existing `self.skipTest(...)`
calls for fixtures the current Sena 3 snapshot doesn't happen to contain
(e.g. "no pronunciation with media files found") -- unchanged from the
original test design, not something introduced or suppressed by this task.
