# Live evidence -- #352 DataNotebook face (Title/Text)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_datanotebook_live.py -m requires_live_project -q
```

## Pre-fix live probe (read-only shapes, target_sandbox)

- `Title` pytype=`ITsString`, `hasattr(Title, 'get_String')`=False --
  bare ITsString, not IMultiString (snapshot 19163 confirmed live).
- `hasattr(record, 'Text')`=False -- no `Text` member at all.
- Fresh `DescriptionOA`/`TextRA` are None (created on demand).

## Fix (`flexicon/code/Notebook/DataNotebookOperations.py`)

- Title (8 sites: Create, Find, GetTitle, SetTitle, CreateSubRecord,
  Duplicate, _DuplicateSubRecordInto, GetSyncableProperties): read via
  house `_ReadTsString`, write via `_MakeTsString`, duplicate by direct
  assignment (same idiom as `TextOperations.Duplicate` para Contents).
- Content (7 `record.Text.*` sites): body lives in `DescriptionOA`
  paragraphs -- new `_ReadRecordContent` / `_SetRecordContent` /
  `_CopyRecordContent` helpers (paragraph Contents round-trip preserves
  WS runs). Docstrings updated (Title is single-valued; Content is
  DescriptionOA paragraphs).
- Adjacent bugs found live while verifying (required by the fix):
  `GetAll` enumerated `IRnResearchNbkRepository` (yielded the notebook
  itself) -- now iterates `ResearchNotebookOA.RecordsOC`;
  `Duplicate` treated the notebook owner as a record parent -- now
  mirrors `Delete`'s `hasattr(SubRecordsOS)` dispatch;
  `GetSyncableProperties` called nonexistent `__ResolveObject` -- now
  `__GetRecordObject`.

## Post-fix values read back from the LCM

- `Create("TEST_352 title", content="First paragraph.\nSecond paragraph.")`
  then `GetTitle` == title, `GetContent` == content, `Find` hits,
  `GetSyncableProperties` `{"Title": title, "Text": content}`.
- `SetTitle`/`SetContent` round-trip incl. clearing to `""`.
- `Duplicate(deep=True)` conserves title + content;
  `CompareTo(rec, dup)` reports no differences.
- Sub-record create conserves title + content.

## Pass/fail

**PASS.** `4 passed` on the command above, live run_mode.
