# Issue #880 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/880-infltype-feats-slots-sync from origin/fix/878-infltype-gloss-sync (`53c8f4d3`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#878 each have open PRs #853–#879)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #880** (new this run): `GetTypeSyncableProperties` omitted **InflFeatsOA** and **SlotsRC** on **LexEntryInflType** -- sibling slice from **#878** out-of-scope / **#826**.

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. Extend **GetTypeSyncableProperties** on `VariantOperations` for `LexEntryInflType`:
   - When `InflFeatsOA` is non-null, emit **InflFeats** / **InflFeatsGuid** via `_GetFeatureStruc` (C4); do not route through `FEATURE_STRUC_OWNER_TABLE` (LexEntryInflType is excluded there by design).
   - When `SlotsRC` is non-empty, emit **slots_rc** as ordered slot GUID strings.
2. **ApplyTypeSyncableProperties** pops **InflFeats**, **InflFeatsGuid**, and **slots_rc** before delegating multistrings to `BaseOperations.ApplySyncableProperties` (C6).
3. Apply **InflFeats** with `_ApplyFeatureStruc(..., "InflFeatsOA", ..., on_unresolved="raise")`.
4. Apply **slots_rc** by resolving each GUID to `IMoInflAffixSlot`, then `SlotsRC.Clear()` + `Add` inside `_TransactionCM`.
5. Tag the emission block with `issue #880` in comments.

**Out of scope:** plain `LexEntryType` scalar fields; live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue880_infltype_feats_slots_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue880_infltype_feats_slots_sync_live.py -m requires_live_project -q` on `target_sandbox`.
