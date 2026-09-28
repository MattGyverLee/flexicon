# Live evidence -- #352 Media + LexEntry-etymology faces

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_media_etym_live.py -m requires_live_project -q
```

## Audit correction: the Media rows were misclassified

The issue checked `ICmMedia` (Label, no Description/Copyright), but
every flagged call site handles **ICmFile**: `MediaOperations`
creates via `ICmFileFactory` ("media file" throughout),
`LexEntryOperations:462-464` and `PronunciationOperations:367-369`
duplicate `MediaFilesOS` members via `ICmFileFactory`. Snapshot for
**ICmFile**: `Description` IMultiString, `Copyright` IMultiString,
`InternalPath` String -- so `Description.CopyAlternatives`,
`get_String`/`set_String`, and the `hasattr(media, "Copyright")`
guard are all correct and need no change. The `Label`-named methods
read/write the file `Description` field.

## Real bugs found live in the same pass (fixed)

- `MediaOperations.Duplicate` set the " (copy)" label in `Create()`,
  then `CopyAlternatives` overwrote it with the source Description --
  the suffix was silently lost. Now re-applied after the copy.
- `MediaOperations.CompareTo` called `self.project._CompareValues`,
  which does not exist on FLExProject (AttributeError on every
  compare) -- now inline `!=` like the DataNotebook/Person/SemDom
  CompareTo methods. (8 sibling call sites in other files noted as
  follow-up; out of #352 scope.)
- `MediaOperations.Delete` called `self.project.cache...` (no lowercase
  `cache` member) -- now `media.Delete()` in a transaction.
- `LexEntryOperations.Duplicate:471` copied nonexistent etymology
  `Source` (unguarded -- raised on any entry with an etymology); now
  copies `LanguageNotes`, mirroring `EtymologyOperations.Duplicate`.

## Post-fix values read back from the LCM

- `Create(path, label)` -> `GetLabel` round-trips; `SetLabel`
  round-trips; `Duplicate` label == source + " (copy)"; sync props
  carry InternalPath + Description dict; self-compare clean.
- Entry with etymology (`source`/`form`/`gloss`) duplicates cleanly;
  dup etymology reads back source/form via `Etymology.GetSource/GetForm`.

## Pass/fail

**PASS.** `2 passed` on the command above, live run_mode.
Related suite `test_media_add_picture_owned_cmfile.py`: 1 passed.
(`tests/phase4_system_shared_tests.py` fails collection with
`ModuleNotFoundError: test_validation_base` -- pre-existing, unrelated.)
