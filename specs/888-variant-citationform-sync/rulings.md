# Issue #888 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/888-variant-citationform-sync from origin/fix/886-variant-lexemeform-sync (`84e64e54`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#886 each have open PRs #853–#887)
- Selected **P2 #888** (new this run): `GetSyncableProperties` on **ILexEntryRef** omits owning-entry **CitationForm** -- sibling slice from **#886** out-of-scope / **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In **GetSyncableProperties**, emit **CitationForm** as a `{ws_id: text}` dict read from the owning entry's **CitationForm** IMultiString (non-empty alts only, `normalize_text`), matching **LexEntryOperations** shape.
2. In **ApplySyncableProperties**, pop **CitationForm** before the base loop; after ref scalars / RS rebuild (#884) and optional **LexemeForm** (#886), delegate **CitationForm** to **LexEntryOperations.ApplySyncableProperties** on `_GetTypedOwner(variant)` with the same `ws_map` / `fill_gaps`. When both **LexemeForm** and **CitationForm** are present, one delegation with both keys is acceptable.
3. Tag the **CitationForm** emission block with `issue #888` in comments.
4. Do not change **GetTypeSyncableProperties**, ILexEntryRef RS keys (#884), or **LexemeForm** (#886) in this PR.

**Out of scope:** Comment, Bibliography, and other entry multistrings not yet sliced from **#826**; live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue888_variant_citationform_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue888_variant_citationform_sync_live.py -m requires_live_project -q` on `target_sandbox`.
