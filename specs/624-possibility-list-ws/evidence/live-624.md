# Live verification -- issue #624 (possibility-list Operations name paths)

Date: 2026-10-02
Project: Sena 3 via `sena3_sandbox` (tempdir copy of the .fwbackup; nothing leaks)

## Command

```
cd C:/Github/flexicon/.claude/worktrees/i624
$env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_issue624_possibility_list_name_ws_live.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"`

## Pre-state / post-state (raw LCM `get_String`, bypassing flexicon)

Sena 3: DefaultAnalysisWritingSystem = `pt`, CurrentAnalysisWritingSystems = [pt, en],
vernacular = [seh, seh-fonipa-x-etic]. List text lives only in `en`.

| Check | Value read back from LCM |
|-------|--------------------------|
| pre: Publication Name pt / en | `''` / `'Main Dictionary'` |
| pre: PossibilityList Name pt / en | `''` / `'Parts Of Speech'` |
| pre: Anthropology item Name pt / en | `''` / `'Project Variables'` |
| pre: Person Name en, no vernacular text | `'Default User'` |
| `Publications.GetName` / `Find('Main Dictionary')` (no ws) | `'Main Dictionary'` / found (old code: `''` / `None`) |
| `PossibilityLists.FindList('Parts Of Speech')`, `GetListName` | found / `'Parts Of Speech'` |
| `Anthropology.GetName`, `Find` | `'Project Variables'` / found |
| `Person.GetName`, `Find('Default User')` | `'Default User'` / found |
| `TranslationTypes`, `Agents`, `PossibilityLists.FindItem/GetItemName/GetSyncableProperties` | en text returned / found |
| Any `Find*(name, wsHandle=pt)` | `None` (explicit ws stays exact); `GetName(.., pt)` -> `''` |
| `Location.Create('TEST_Site', wsHandle=en)` then re-read | post: en=`'TEST_Site'`, pt=`''`; `GetName` -> `'TEST_Site'`; `Find` finds it; `Find(.., pt)` -> `None` |
| `Publications.Create('TEST_Pub', wsHandle=en)`, `SetName(item, 'TEST_PubDefault')` (no ws), re-fetched via `Find` | post: pt=`'TEST_PubDefault'`, en=`'TEST_Pub'`; `GetName` -> `'TEST_PubDefault'`; both names findable |

Control: with the fix stashed (`git stash push -- flexicon/code`), the same live file gives `9 failed`.

## Result

`9 passed in 17.04s` (live, run_mode live)

Offline: `python -m pytest -m "not requires_live_project" -q` -> `3659 passed, 1151 deselected`
(includes 33 new tests in `tests/operations/test_issue624_possibility_list_name_ws.py`).
