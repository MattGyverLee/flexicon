# Live verification -- issue #604 (SemanticDomainOperations name paths)

Date: 2026-10-02
Project: Sena 3 via `sena3_sandbox` (tempdir copy of the .fwbackup; nothing leaks)

## Command

```
cd C:/Github/flexicon/.claude/worktrees/p2-604
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue604_semdom_name_ws_live.py -m requires_live_project -q -s
```

`tests/live_status.json` -> `"run_mode": "live"`

## Pre-state / post-state (raw LCM `get_String`, bypassing flexicon)

Sena 3: DefaultAnalysisWritingSystem = `pt`, CurrentAnalysisWritingSystems = [pt, en].

| Check | Value read back from LCM |
|-------|--------------------------|
| pre: domain 7.2.1.1 Name in default WS (pt) | `''` |
| pre: domain 7.2.1.1 Name in `en` | `'Walk'` |
| `GetName(domain)` (no ws) | `'Walk'` (old code: `''`) |
| `GetQuestions(domain)` (no ws) | 1220 chars == raw `en` questions (old code: empty) |
| `FindByName('Walk')` / upper-case / after switching default analysis to a fresh text-less `fr` WS | found, `GetNumber == '7.2.1.1'` |
| `FindByName('Walk', wsHandle=pt)` | `None` (explicit ws stays exact) |
| `Create('TEST_Custom','900.604', wsHandle=en)` then `SetName(.., 'TEST_Renamed', wsHandle=en)`; domain re-fetched with `Find('900.604')` | post: en=`'TEST_Renamed'`, pt=`''`; `GetName` -> `'TEST_Renamed'`; `FindByName` finds it |
| `SetName(custom, 'TEST_Default')` (no ws) re-fetched | pt=`'TEST_Default'`, en=`'TEST_Base'`; `GetName` -> `'TEST_Default'` |

Control: with the fix stashed, the same live file gives `8 failed, 1 passed`.

## Result

`9 passed in 20.38s` (live)

Offline: `python -m pytest -m "not requires_live_project" -q` -> `2832 passed, 1125 deselected`
(includes the 18 new tests in `tests/operations/test_issue604_semdom_name_ws.py`).
