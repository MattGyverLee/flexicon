# Live evidence -- #352 AnnotationDef face (HelpString/Prompt)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_annodef_live.py -m requires_live_project -q
```

## Pre-fix classification (snapshot + live hasattr)

- Snapshot: `ICmAnnotationDefn` declares only Boolean/Int32
  (`PromptUser`, `AllowsComment`, ...); no `HelpString`/`Prompt` on it,
  on `ICmPossibility`, or anywhere in the baseline file.
- Live on a fresh def: `hasattr HelpString`=False, `hasattr Prompt`=False,
  `hasattr Description`=True (inherited IMultiString from ICmPossibility).
- Side finding: the `CmAnnotationType` enum is not exposed via pythonnet
  (`from SIL.LCModel import CmAnnotationType` raises ImportError), so
  several docstring examples are stale; `Create()` also only applies the
  passed type behind an always-False `hasattr(AnnotationType)` guard.
  Out of #352 scope; noted, not changed.

## Fix (`flexicon/code/System/AnnotationDefOperations.py`)

- `GetHelpString`/`SetHelpString`/`GetPrompt`/`SetPrompt`: read/write the
  inherited `Description` multistring (were `get/set_String` on missing
  members -- getters permanently "", setters permanent no-ops).
- `Duplicate`/`_DuplicateSubDefInto`: copy `Description` (dropped the
  dead guarded HelpString/Prompt copies).
- `GetSyncableProperties`: both keys read `Description`.
- Docstrings updated (storage mapping + Duplicate notes).

## Post-fix values read back from the LCM

- Fresh def: both getters ""; `SetHelpString` round-trips;
  `SetPrompt` round-trips; sync props carry the text under both keys.
- `Duplicate` conserves the description text.

## Pass/fail

**PASS.** `3 passed` on the command above, live run_mode.
