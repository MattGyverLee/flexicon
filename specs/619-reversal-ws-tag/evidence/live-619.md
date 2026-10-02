# Live verification: issue #619 (ReversalIndexOperations.Create stores WS tag)

Project: `target_sandbox` (tempdir copy of the Target .fwbackup). Worktree
`p2-619`, branch `fix/619-reversal-ws-tag`.

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 PYTHONPATH=<worktree> python -m pytest \
  tests/operations/test_issue619_reversal_ws_tag_live.py \
  -m requires_live_project -q -s
```

`tests/live_status.json` -> `"run_mode": "live"`

## Pre-state (read back from the LCM)

- Analysis WS: tag `'en'`, handle `999000001`.
- Reversal indexes after clearing any existing `en` index in the sandbox:
  `[]` (no stored WritingSystem values).

## Before the fix (same test, old `ReversalIndexOperations.py`)

- `Create("TEST_by_handle", 999000001)` then re-query by GUID:
  `IReversalIndex.WritingSystem == '999000001'` (stringified handle).
  Test failed: `AssertionError: assert '999000001' == 'en'`.
- `Create(..., 'en')` then `FindByWritingSystem(999000001)` -> not found (failed).

## Post-state (after the fix, read back from the LCM by GUID)

- Create by handle: `WritingSystem == 'en'` (all indexes: `['en']`);
  `FindByWritingSystem('en')` and `FindByWritingSystem(999000001)` both return
  the created index (same GUID); `GetWritingSystem(idx) == 'en'`.
- Create by tag `'en'`: `WritingSystem == 'en'`; both lookup forms find it.
- Duplicate `Create` by tag or by handle raises `FP_ParameterError`, index list unchanged.
- `ReversalEntries.Create(index, "TEST_form")` with no explicit wsHandle resolves
  the WS from the index and reads back `'TEST_form'`.

## Result

`4 passed` (test_issue619_reversal_ws_tag_live.py). Related live files
(`test_guid_create_agent_reversals_live.py`, `test_reversal_index_create_analysis_ws_live.py`):
combined run `20 passed, 1 skipped` (skip = dup-GUID-across-two-indexes needs 2 analysis
WSs; Target has 1; same skip as baseline).

Offline: `python -m pytest -m "not requires_live_project" -q` -> `2829 passed, 1120 deselected`.

PASS
