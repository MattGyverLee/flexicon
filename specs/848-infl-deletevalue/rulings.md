# Issue #848 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/848-infl-deletevalue from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs #833, #834, #836, #840, #842, #844, #846 each have open PRs (#837–#839, #841, #843, #845, #847).
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #848** (new): `InflectionFeatureOperations` lacked `DeleteValue` while `CreateValue` exists — inflection value deletes still hit raw `ValuesOC` proxy gaps fixed on phonology in #816/#844.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Add `DeleteValue` on `InflectionFeatureOperations` with HVO membership scan on `ValuesOC`, matching post-#844 phonology control flow.
2. Raise `FP_ParameterError` when no slot matches; do not use bare `except Exception: pass` on the membership path.
3. Tag the membership block with `issue #848` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths in this PR.

**Out of scope:** Complex-feature value surfaces; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue848_infl_deletevalue_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue848_infl_deletevalue_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
