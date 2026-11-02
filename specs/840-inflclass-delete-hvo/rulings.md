# Issue #840 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/840-inflclass-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR.
- Open **P2** bugs #833, #834, #836 each have open PRs (#837–#839).
- No open **P3** bugs.
- Selected **P2 #840** (new): `InflectionFeatureOperations.InflectionClassDelete` bare-proxy `SubclassesOC` / `InflectionClassesOC` `.Remove` -- sibling gap named in #820 lex-lead ruling.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

`InflectionFeatureOperations.InflectionClassDelete` must resolve collection membership by **HVO** before mutating, matching #820 FeatureDelete / #816 PhonFeature Delete.

**Fix for this PR:**

1. After resolving `owning`, scan the sequence for a slot whose `Hvo` matches the resolved class; `Remove` the matched member.
2. Raise `FP_ParameterError` if no member found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue840_*`.

**Out of scope:** Other InflectionFeatureOperations write paths; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue840_inflclass_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue840_inflclass_delete_hvo_live.py -m requires_live_project -q` on `target_project`.
