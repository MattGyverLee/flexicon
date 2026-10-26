# Issue #722 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #722 (P2) -- LexSenseOperations AddDomainType / RemoveDomainType DomainTypesRC HVO membership  
**Parent triage:** #720 UsageTypesRC sibling gap (other LexSense RC fields out of scope)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#722** filed this run (LexSense DomainTypesRC sibling gap)

Untrusted open issues ignored per automation policy (e.g. #635 from rulingAnts).

## RULING (binding)

1. In `AddDomainType`, treat a domain type as already linked when any member of `DomainTypesRC` shares `domain_type.Hvo`, not `domain_type in DomainTypesRC`.
2. In `RemoveDomainType`, scan `DomainTypesRC` for matching `Hvo`, then call `Remove` on the collection member from the loop.
3. Tag both lookups with `issue #722` in comments.
4. Do not refactor unrelated LexSense RC membership sites in this PR.

**Out of scope:** AnthroCodesRC, DoNotPublishInRC, and other HVO-family gaps.

## Verification plan

- Offline: `tests/operations/test_issue722_lexsense_domaintype_hvo_offline.py`
- Live: `tests/operations/test_issue722_lexsense_domaintype_hvo_live.py`
- Evidence: `specs/722-lexsense-domaintype-hvo/evidence/`
