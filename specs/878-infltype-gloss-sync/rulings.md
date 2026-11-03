# Issue #878 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/878-infltype-gloss-sync from origin/main (`91be3a73`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#876 each have open PRs #853–#877)
- Open **P3** bugs without an open PR: **none**
- **#850** / **#776** remain open but fixes landed on main via PR #851 / #877; not selected.
- Selected **P2 #878** (new this run): `VariantOperations` had no entry-type sync surface; **LexEntryInflType** gloss bracket fields **GlossPrepend** / **GlossAppend** omitted -- sibling slice from **#876** out-of-scope / **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Add **GetTypeSyncableProperties** / **ApplyTypeSyncableProperties** on `VariantOperations` for `ILexEntryType` inputs (resolve via `cast_to_concrete`, accept `LexEntryType` and `LexEntryInflType`).
2. When `ClassName == LexEntryInflType`, emit **GlossPrepend** and **GlossAppend** as `{ws_id: text}` multistring dicts (analysis WS ids, non-empty alts only).
3. **ApplyTypeSyncableProperties** delegates to `BaseOperations.ApplySyncableProperties` on the resolved type (multistring + `ws_map` behaviour unchanged).
4. Tag the emission block with `issue #878` in comments.
5. Do not refactor `GetSyncableProperties` (ILexEntryRef) or unrelated variant paths in this PR.

**Out of scope:** `InflFeatsOA` / `SlotsRC` on `LexEntryInflType`; plain `LexEntryType` scalar fields beyond empty dict; live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue878_infltype_gloss_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue878_infltype_gloss_sync_live.py -m requires_live_project -q` on `target_sandbox`.
