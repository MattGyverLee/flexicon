# Issue #884 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/884-variant-ref-rs-sync from origin/fix/882-lexentrytype-type-sync (`a74ee63b`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#882 each have open PRs #853–#883)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #884** (new this run): `GetSyncableProperties` on **ILexEntryRef** omits RS membership -- sibling slice from **#882** out-of-scope / **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In **GetSyncableProperties**, emit ordered GUID lists for **VariantEntryTypesRS**, **ComponentLexemesRS**, **ComplexEntryTypesRS**, and **PrimaryLexemesRS** (empty list when the RS property is absent). Keep existing **show_complex_forms_in_rs** emission.
2. Add **ApplySyncableProperties** on `VariantOperations` that pops RS keys, delegates scalars to `BaseOperations`, then rebuilds each RS via `Clear()` + `Add()` after GUID resolution (warn-and-skip missing GUIDs, same policy as `LexReferenceOperations.targets_rs`).
3. Tag the RS emission block with `issue #884` in comments.
4. Do not change **GetTypeSyncableProperties** / **ApplyTypeSyncableProperties** (**#878**–**#882**) in this PR.

**Out of scope:** owning-entry **LexemeFormOA** form text (separate surface); live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue884_variant_ref_rs_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue884_variant_ref_rs_sync_live.py -m requires_live_project -q` on `target_sandbox`.
