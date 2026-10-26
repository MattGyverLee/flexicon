# Issue #644 -- verification evidence

## Offline

```text
python3 -m pytest tests/operations/test_issue644_pronunciation_duplicate_hvo_offline.py -q
```

Result: **PASS** (2 passed)

## Live

```text
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue644_pronunciation_duplicate_hvo_live.py -m requires_live_project -q
```

Result: **FAIL: unverified** -- cloud agent has no `clr` / FieldWorks LCM runtime.

`tests/live_status.json`: not produced (live suite not executed).
