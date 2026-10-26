# Issue #650 -- verification evidence

## Offline

```text
PYTHONPATH=. python3 -m pytest tests/operations/test_issue650_datanotebook_duplicate_hvo_offline.py -q
```

Result: **PASS** (2 passed)

## Live

```text
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue650_datanotebook_duplicate_hvo_live.py -m requires_live_project -q
```

Result: **FAIL: unverified** -- cloud agent has no `clr` / FieldWorks LCM runtime.

`tests/live_status.json`: not produced (live suite not executed).
