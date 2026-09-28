# Live evidence -- #546 Allomorph GetIsAbstract / SetIsAbstract

Date: 2026-09-26
Branch: `fix/546-allomorph-isabstract` (worktree `C:/Github/flexicon-546`, based on `19b9c9e`)
Fixture: `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`)

## Commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue546_allomorph_isabstract_live.py -m requires_live_project -q
```

Result: `5 passed in 2.99s`. `tests/live_status.json`: `"run_mode": "live"`.

```
python -m pytest -m "not requires_live_project" -q
```

Result: `2457 passed, 1016 deselected` (full offline gate, zero failures).

Targeted Allomorph-adjacent run (subset of the above, kept for reference):

```
python -m pytest -q -m "not requires_live_project" tests/operations/test_issue546_allomorph_isabstract_offline.py tests/test_allomorph_wrappers.py tests/operations/test_allomorph_owner.py tests/operations/test_t8_allomorph_feature_sync.py tests/operations/test_t8_allomorph_hasattr_allowlist.py
```

Result: `63 passed, 6 deselected`.

## Pre/post values read back from the LCM

Each value was re-queried after the write via `sandbox.Object(hvo)` + `GetIsAbstract`.

| Step | Re-read `IsAbstract` |
|------|----------------------|
| `Allomorphs.Create(entry, ..., morphType="suffix")` (alternate) | `False`; lexeme form also `False` |
| `SetIsAbstract(allo, True)` | `True` (object and `Object(hvo)` re-read) |
| `SetIsAbstract(allo, False)` | `False` |
| `SetIsAbstract(lexeme, True)` where `lexeme = entry.LexemeFormOA` | `True` (object and `Object(hvo)` re-read) |
| `SetIsAbstract(hvo_int, True)` then `GetIsAbstract(wrapper)` | `True`; `SetIsAbstract(wrapper, False)` then `GetIsAbstract(hvo)` -> `False` |
| `Duplicate(abstract_allo)` | `GetIsAbstract(dup)` -> `True` |

PASS
