# Issue #882 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/882-lexentrytype-type-sync from origin/fix/880-infltype-feats-slots-sync (`47e37218`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#880 each have open PRs #853–#881)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #882** (new this run): `GetTypeSyncableProperties` returns `{}` for plain **LexEntryType** -- sibling slice from **#880** out-of-scope / **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In **GetTypeSyncableProperties**, when `ClassName == "LexEntryType"`, emit **Name**, **Abbreviation**, **Description**, and **ReverseAbbr** as `{ws_id: text}` multistring dicts (analysis WS ids, non-empty alts only).
2. Do not change **LexEntryInflType** emission (**#878** / **#880**); keep the early `LexEntryInflType`-only block for gloss / InflFeats / slots.
3. **ApplyTypeSyncableProperties** already delegates plain types to `BaseOperations.ApplySyncableProperties`; no override needed.
4. Tag the **LexEntryType** emission block with `issue #882` in comments.
5. Do not refactor ILexEntryRef `GetSyncableProperties` or unrelated variant paths in this PR.

**Out of scope:** inflection closed-feature GSP (**#876** follow-up); live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue882_lexentrytype_type_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue882_lexentrytype_type_sync_live.py -m requires_live_project -q` on `target_sandbox`.
