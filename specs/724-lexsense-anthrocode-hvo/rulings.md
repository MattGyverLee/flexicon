# Issue #724 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #724 (P2) -- LexSenseOperations AddAnthroCode / RemoveAnthroCode AnthroCodesRC HVO membership  
**Parent triage:** #718 SemanticDomainsRC fix explicitly left AnthroCodesRC out of scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#724** filed this run (LexSense AnthroCodesRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddAnthroCode`, treat a code as already linked when any member of `sense.AnthroCodesRC` shares `anthro_code.Hvo`, not `anthro_code in AnthroCodesRC`.
2. In `RemoveAnthroCode`, locate the reference-collection member by matching `Hvo`, then call `Remove` on that member.
3. Tag both lookups with `issue #724` in comments.
4. Do not refactor unrelated LexSense RC membership sites in this PR.

**Out of scope:** DoNotPublishInRC, UsageTypesRC, DomainTypesRC, and other LexSense RC HVO gaps.

## Verification plan

- Offline: `tests/operations/test_issue724_lexsense_anthrocode_hvo_offline.py`
- Live: `tests/operations/test_issue724_lexsense_anthrocode_hvo_live.py`
- Evidence: `specs/724-lexsense-anthrocode-hvo/evidence/`
