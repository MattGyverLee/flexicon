# Issue #886 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/886-variant-lexemeform-sync from origin/fix/884-variant-ref-rs-sync (`8bef9234`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#884 each have open PRs #853–#885)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #886** (new this run): `GetSyncableProperties` on **ILexEntryRef** omits owning-entry **LexemeForm** -- sibling slice from **#884** out-of-scope / **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In **GetSyncableProperties**, emit **LexemeForm** as a `{ws_id: text}` dict read from the owning entry's **LexemeFormOA.Form** (non-empty alts only, `normalize_text`), matching **LexEntryOperations** shape.
2. In **ApplySyncableProperties**, pop **LexemeForm** before the base loop; after ref scalars / RS rebuild (#884), delegate **LexemeForm** to **LexEntryOperations.ApplySyncableProperties** on `_GetTypedOwner(variant)` with the same `ws_map` / `fill_gaps`.
3. Tag the **LexemeForm** emission block with `issue #886` in comments.
4. Do not change **GetTypeSyncableProperties** or ILexEntryRef RS keys (#884) in this PR.

**Out of scope:** CitationForm and other entry fields not tied to variant surface form; live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue886_variant_lexemeform_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue886_variant_lexemeform_sync_live.py -m requires_live_project -q` on `target_sandbox`.
