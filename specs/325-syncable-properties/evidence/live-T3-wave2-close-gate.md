# Wave-2 live verification -- close gate for #325

**Date:** 2026-09-22  
**Worktree:** `C:/Github/flexicon-325`  
**Branch:** `fix/325-syncable-properties`

## Commands

```
python -m pytest -m "not requires_live_project" -q   # ratchet: 73 passed, 1 skipped
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_325_syncable_properties_live.py -m requires_live_project -q
# -> 9 passed
```

## `tests/live_status.json`

`"run_mode": "live"` (timestamp 2026-09-22T22:45:44Z)

## Gaps closed

| Gap | Pre-state | Post-state (LCM read-back) | Result |
|-----|-----------|----------------------------|--------|
| R1 LanguageRS Apply | LanguagesOA empty; Apply re-read skipped | Seeded 2 LanguagesOA possibilities; `LanguageRS after Apply` matched seeded GUID list | PASS |
| R4 media_uris | FAIL: unverified / xfail | Seeded `MediaFilesOA`+`MediaURI` (own before set); GSP then Apply; re-read `MediaURIsOC` = `file:///TEST_325_media_roundtrip.mp3` | PASS |
| R3 mutating targets_rs | Idempotent only; Clear+Add NRE | Reverse of 3 targets via Remove+rotate (never Clear); re-read matched reversed GUID list | PASS |

## Code fixes in this wave

1. `TextOperations.ApplySyncableProperties`: `ICmMediaContainerFactory` + `ICmMediaURIFactory`; Add to `MediaURIsOC` before `set_MediaURI`.
2. `LexReferenceOperations.ApplySyncableProperties`: replace `TargetsRS` without `Clear()` (Clear permanently breaks `get_TargetsRS`).
3. `LexReferenceOperations.CreateType`: do not replace `ReferencesOA` when the list already exists (else-branch bug).

## RESULT

PASS -- all seven original #325 sites fixed and live-verified with LCM read-back. Close gate open (`closes #325`).
