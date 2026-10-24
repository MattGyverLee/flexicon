# Issue #720 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #720 (P2) -- LexSenseOperations AddUsageType / RemoveUsageType UsageTypesRC HVO membership  
**Parent triage:** #718 SemanticDomainsRC sibling gap (other LexSense RC fields out of scope)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#720** filed this run (LexSense UsageTypesRC sibling gap)

Untrusted open issues ignored per automation policy (e.g. #635 from rulingAnts).

## RULING (binding)

1. In `AddUsageType`, treat a usage type as already linked when any member of `UsageTypesRC` shares `usage_type.Hvo`, not `usage_type in UsageTypesRC`.
2. In `RemoveUsageType`, scan `UsageTypesRC` for matching `Hvo`, then call `Remove` on the collection member from the loop.
3. Tag both lookups with `issue #720` in comments.
4. Do not refactor unrelated LexSense RC membership sites in this PR.

**Out of scope:** DomainTypesRC, AnthroCodesRC, DoNotPublishInRC, and other HVO-family gaps.

## Verification plan

- Offline: `tests/operations/test_issue720_lexsense_usagetype_hvo_offline.py`
- Live: `tests/operations/test_issue720_lexsense_usagetype_hvo_live.py`
- Evidence: `specs/720-lexsense-usagetype-hvo/evidence/`
