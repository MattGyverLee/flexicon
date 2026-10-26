# Issue #718 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #718 (P2) -- LexSenseOperations AddSemanticDomain / RemoveSemanticDomain SemanticDomainsRC HVO membership  
**Parent triage:** #716 Reversal SensesRS sibling gap (LexSense SemanticDomainsRC explicitly out of scope there)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#718** filed this run (LexSense SemanticDomainsRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddSemanticDomain`, treat a domain as already linked when any member of `sense.SemanticDomainsRC` shares `domain.Hvo`, not `domain in SemanticDomainsRC`.
2. In `RemoveSemanticDomain`, locate the reference-collection member by matching `Hvo`, then call `Remove` on that member.
3. Tag both lookups with `issue #718` in comments.
4. Do not refactor unrelated LexSense RC membership sites in this PR.

**Out of scope:** UsageTypesRC, DomainTypesRC, AnthroCodesRC, DoNotPublishInRC, and other LexSense RC HVO gaps.

## Verification plan

- Offline: `tests/operations/test_issue718_lexsense_semanticdomain_hvo_offline.py`
- Live: `tests/operations/test_issue718_lexsense_semanticdomain_hvo_live.py`
- Evidence: `specs/718-lexsense-semanticdomain-hvo/evidence/`
