# Issue #481 live verification

## Command

```bash
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue481_lexref_resolver_cast_live.py -m requires_live_project -q
```

## run_mode

See `tests/live_status.json` after the run.

## Pre/post state

- Pre: `GetMappingType(ref_type.Hvo)` must fail or mis-read if resolvers return uncast `ICmObject` (MappingType not on static ICmObject view).
- Post: same call returns a mapping string for a genuine LexRefType HVO from Sena 3 sandbox.

## Result

**FAIL: unverified** -- cloud agent has no mono/.NET FLEx runtime (`FLEXLIBS_REQUIRE_LIVE=1` hard-fails in `tests/flex_plugin.py`).

Offline ratchet: **PASS** (2/2) -- `python3 -m pytest tests/operations/test_issue481_lexref_resolver_cast_offline.py -m "not requires_live_project" -q`
