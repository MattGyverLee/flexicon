# Issue #876 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/876-phon-gloss-sync from origin/main (`91be3a73`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#874 each have open PRs #853–#875)
- Open **P3** bugs without an open PR: **none**
- **#826** (MattGyverLee) remains open; grammar Adjacency is in open PR **#875** (#874); StrucChange in **#873** (#872).
- Selected **P2 #876** (new this run): `PhonFeatureOperations.GetSyncableProperties` never emits **GlossAbbreviation**, **RightGlossSep**, or **ShowInGloss** -- sibling slice from **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In `GetSyncableProperties`, after existing multistring fields, emit **GlossAbbreviation** and **RightGlossSep** via the existing `__ReadMultiString` helper (IMultiUnicode, same read path as Name).
2. When `hasattr(feat, "ShowInGloss")`, emit **ShowInGloss** as `bool(feat.ShowInGloss)`.
3. Do not override `ApplySyncableProperties`; the base loop already applies multistring dicts and bool scalars.
4. Tag the emission block with `issue #876` in comments.
5. Do not refactor Values co-create or IFsClosedFeature guard paths in this PR.

**Out of scope:** LexEntryInflType GlossPrepend/GlossAppend; inflection-feature GSP if added later; live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue876_phon_gloss_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue876_phon_gloss_sync_live.py -m requires_live_project -q` on `target_sandbox`.
