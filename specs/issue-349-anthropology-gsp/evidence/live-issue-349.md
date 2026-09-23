# Live verification — issue #349 Anthropology GetSyncableProperties

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/test_pattern_writing_systems_enumeration.py -m requires_live_project -q
```

(or any harness that calls `AnthropologyOperations.GetSyncableProperties` on a real `ICmAnthroItem`)

## run_mode

**FAIL: unverified** — Cloud Agent Linux pod has no libmono / FieldWorks LCM runtime (`RuntimeError: Could not find libmono`). Offline source ratchet passed instead:

```
python3 -m pytest tests/operations/test_anthropology_get_syncable_properties.py -m "not requires_live_project" -q
# 2 passed
```

## Pre-state (reported in issue #349)

`GetSyncableProperties` → `AttributeError: 'AnthropologyOperations' object has no attribute '_AnthropologyOperations__ResolveObject'` on every item.

## Post-state (expected after fix, not read back from LCM here)

`GetSyncableProperties(item)` resolves via `__GetItemObject` and returns a dict with `Name`, `Abbreviation`, `Description`, `AnthroCode`, `Category` keys.

## Result

**FAIL: unverified** (live LCM read-back not performed in this environment).
