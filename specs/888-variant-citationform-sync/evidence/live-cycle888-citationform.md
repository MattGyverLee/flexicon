# Live verification — issue #888

**Date:** 2026-11-03  
**Issue:** #888 VariantOperations CitationForm sync  
**Branch:** fix/888-variant-citationform-sync

## Commands

```bash
python3.12 -m pytest tests/operations/test_issue888_variant_citationform_sync_offline.py -m "not requires_live_project" -q
FLEXLIBS_REQUIRE_LIVE=1 python3.12 -m pytest tests/operations/test_issue888_variant_citationform_sync_live.py -m requires_live_project -q
```

## Offline

- Result: **PASS** (3/3)

## Live

- `tests/live_status.json` `run_mode`: **mock** (no FieldWorks / clr on cloud agent)
- Result: **FAIL: unverified** — live LCM round-trip not executed

## Expected live behavior (when run on Target sandbox)

1. Create variant ref with distinct CitationForm on owning entry.
2. `GetSyncableProperties` returns WS-keyed CitationForm dict.
3. `ApplySyncableProperties` with `ws_map` writes CitationForm on target owning entry; re-read from LCM confirms value.
