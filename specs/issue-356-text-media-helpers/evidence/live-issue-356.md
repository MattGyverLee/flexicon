# Issue #356 live evidence -- TextOperations media helpers

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue356_text_media_helpers.py -m requires_live_project -q
```

## run_mode

See `tests/live_status.json` after the run (`run_mode` must be `"live"`).

## Pre-state

New text in `target_sandbox` with no `MediaFilesOA` container.

## Post-state (read back from LCM)

After `AddMediaFile` + repository re-fetch by GUID:

- `GetMediaFiles(refetched)` returned at least one entry.
- `cast_to_concrete(refetched).MediaFilesOA.MediaURIsOC.Count >= 1`.
- `GetSyncableProperties(refetched)["media_uris"]` included a non-empty `file_guid`.

## Result

**FAIL: unverified** on cloud agent runner (2026-09-23).

Blocker: no FieldWorks / libmono on Linux pod -- `FLEXLIBS_REQUIRE_LIVE=1`
pytest errored at session fixture with `RuntimeError: Could not find libmono`.
Offline ratchet passed; live round-trip must run on a Windows FieldWorks host
before merge.

## Offline gate (passed)

```
python3 -m pytest tests/operations/test_issue356_text_media_helpers.py -m "not requires_live_project" -q
```
