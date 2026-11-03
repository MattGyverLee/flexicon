# Issue #872 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/872-metathesis-strucchange-sync from origin/main (`91be3a73`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#870 each have open PRs #853–#871)
- Open **P3** bugs without an open PR: **none**
- **#826** (MattGyverLee) remains open; lexicon/pronunciation/etymology/text scalar sync landed on main via PR **#827**; grammar **PhMetathesisRule.StrucChange** from the #826 field list was still omitted.
- Selected **P2 #872** (new this run): `PhonologicalRuleOperations.GetSyncableProperties` never emits metathesis **StrucChange** -- sibling slice from **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In `GetSyncableProperties`, when `hasattr(rule, "StrucChange")`, emit `StrucChange` via `_ReadTsString` as a plain Python `str` in the returned dict (ITsString on `IPhMetathesisRule`).
2. Do not override `ApplySyncableProperties`; the base loop already applies plain strings to ITsString fields (same as `PronunciationOperations` CVPattern/Tone in #827).
3. Tag the emission block with `issue #872` in comments.
4. Do not refactor unrelated PhonologicalRuleOperations sync or WireRule paths in this PR.

**Out of scope:** Remaining #826 grammar items (Adjacency, LexEntryInflType gloss fields, Fs gloss abbreviations); live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue872_metathesis_strucchange_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue872_metathesis_strucchange_sync_live.py -m requires_live_project -q` on `target_sandbox`.
