# Issue #734 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #734 (P2) -- SemanticDomainOperations GetSensesInDomain SemanticDomainsRC HVO membership  
**Parent triage:** #718 LexSense Add/RemoveSemanticDomain sibling (write path); GetSenseCount already uses Hvo (#106)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#734** filed this run (GetSensesInDomain read-path HVO gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `GetSensesInDomain`, treat a sense as tagged with the domain when any member of `sense.SemanticDomainsRC` shares `domain.Hvo`, not `domain in SemanticDomainsRC`.
2. Reuse the existing `domain_hvo = domain.Hvo` local; do not refactor `GetSenseCount` or LexSense write paths in this PR.
3. Tag the lookup with `issue #734` in comments.

**Out of scope:** LexSense Add/RemoveSemanticDomain (#718 PR #719), overlay/allomorph RC gaps, other SemanticDomain methods.

## Verification plan

- Offline: `tests/operations/test_issue734_semanticdomain_getsenses_hvo_offline.py`
- Live: `tests/operations/test_issue734_semanticdomain_getsenses_hvo_live.py`
- Evidence: `specs/734-semanticdomain-getsenses-hvo/evidence/`
