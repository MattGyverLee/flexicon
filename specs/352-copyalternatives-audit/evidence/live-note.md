# Live evidence -- #352 Note face (Source -> SourceRA agent)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_note_live.py -m requires_live_project -q
```

## Pre-fix live probe (member shapes on a fresh note, target_sandbox)

- `hasattr(note, 'Source')`=False -- no Source multistring.
- `hasattr(note, 'SourceRA')`=True (None when unset).
- Assignment probe: `note.SourceRA = agent` (CmAgent) succeeds;
  `note.SourceRA = person` (CmPerson) raises `TypeError` -- the
  reference targets ICmAgent only.
- Agent `Name` is IMultiUnicode (read via `Agents.Find`/`GetName`, which
  already use `get_String` correctly).

## Fix (`flexicon/code/Notebook/NoteOperations.py`, `annotation.py`)

- `GetAuthor`: returns the SourceRA agent's best-analysis name, "" when
  unset (was `get_String` on a missing member behind always-False
  `hasattr` -- permanently "").
- `SetAuthor(note, author)`: accepts an ICmAgent (direct assign), a name
  string (find-or-create via `Agents.Find`/`Agents.Create`), or ""/None
  to clear (`SourceRA = None`, verified live). Was `set_String` on the
  missing member (always a silent no-op).
- `GetSyncableProperties`: `props["Source"]` is now the agent GUID or
  None (same convention as the neighbouring `AnnotationType` RA key).
- `Annotation.author` wrapper: same agent-name read (was
  `Source.get_String` swallowed by `except Exception`).

## Post-fix values read back from the LCM

- Fresh note author ""; `SetAuthor("TEST_352 Author")` ->
  `GetAuthor` returns the name; a second note with the same name reuses
  the one agent (no duplicates); sync props carry the agent GUID.
- Agent-object assign + `SetAuthor("")` clears to None (read back live).
- `Annotation(note).author` mirrors both states.

## Pass/fail

**PASS.** `3 passed` on the command above, live run_mode.
Related suite `test_note_duplicate.py`: 6 passed.
