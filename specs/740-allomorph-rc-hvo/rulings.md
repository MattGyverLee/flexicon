# Issue #740 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #740 (P2) -- AllomorphOperations PhoneEnvRC / InflectionClassesRC HVO membership  
**Parent triage:** #738 Variant ComponentLexemesRS fix explicitly left Allomorph RC sites out of scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **none on file** -- filed **#740** this run (Allomorph RC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `RemovePhoneEnv`, scan `PhoneEnvRC` for the member whose `Hvo` matches `env.Hvo`, then call `Remove` on that member; if none match, no-op (membership test stays outside the transaction).
2. In `AddInflectionClass`, treat the class as already linked when any `InflectionClassesRC` member shares `infl_class.Hvo`; do not rely on `not in` identity.
3. In `RemoveInflectionClass`, scan by `Hvo` and `Remove(linked)` as in (1).
4. Tag all three sites with `issue #740` in comments.
5. Do not change `AddPhoneEnv` duplicate policy (documented intentional re-add).

**Out of scope:** MSA `ProdRestrictRC`; other HVO gaps with open PRs (#640–#738 family).

## Verification plan

- Offline: `tests/operations/test_issue740_allomorph_rc_hvo_offline.py`
- Live: `tests/operations/test_issue740_allomorph_rc_hvo_live.py`
- Evidence: `specs/740-allomorph-rc-hvo/evidence/`
