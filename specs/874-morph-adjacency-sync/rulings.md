# Issue #874 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/874-morph-adjacency-sync from origin/main (`91be3a73`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#872 each have open PRs #853–#873)
- Open **P3** bugs without an open PR: **none**
- **#826** (MattGyverLee) remains open; lexicon/pronunciation/etymology/text scalar sync landed on main via prior PRs; grammar **PhMetathesisRule.StrucChange** is in open PR **#873** (#872).
- Selected **P2 #874** (new this run): `MorphRuleOperations.GetSyncableProperties` never emits ad hoc co-prohibition **Adjacency** -- sibling slice from **#826**.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In `GetSyncableProperties`, when `hasattr(rule, "Adjacency")`, emit `Adjacency` as `int(rule.Adjacency)` in the returned dict (int scalar on all three `MoAdhocProhib*` concrete types).
2. Do not override `ApplySyncableProperties`; the base loop already applies int scalars (same as `Direction` on phon rules).
3. Tag the emission block with `issue #874` in comments.
4. Do not refactor unrelated MorphRuleOperations sync or prohibition wrapper paths in this PR.

**Out of scope:** Remaining #826 items (LexEntryInflType gloss fields, Fs gloss abbreviations); live proof in cloud when FieldWorks absent (`FAIL: unverified`).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue874_morph_adjacency_sync_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue874_morph_adjacency_sync_live.py -m requires_live_project -q` on `target_sandbox`.
