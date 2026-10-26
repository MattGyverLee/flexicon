# Issue #726 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #726 (P2) -- LexSenseOperations AddDoNotPublishIn / RemoveDoNotPublishIn DoNotPublishInRC HVO membership  
**Parent triage:** #724 AnthroCodesRC fix explicitly left DoNotPublishInRC out of scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#726** filed this run (LexSense DoNotPublishInRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddDoNotPublishIn`, treat a publication as already linked when any member of `sense.DoNotPublishInRC` shares `publication.Hvo`, not `publication in DoNotPublishInRC`.
2. In `RemoveDoNotPublishIn`, locate the reference-collection member by matching `Hvo`, then call `Remove` on that member.
3. Tag both lookups with `issue #726` in comments.
4. Do not refactor unrelated LexSense RC membership sites in this PR.

**Out of scope:** ExampleOperations / LexEntryOperations DoNotPublishInRC, and other LexSense RC HVO gaps with open PRs (#718–#724).

## Verification plan

- Offline: `tests/operations/test_issue726_lexsense_donotpublish_hvo_offline.py`
- Live: `tests/operations/test_issue726_lexsense_donotpublish_hvo_live.py`
- Evidence: `specs/726-lexsense-donotpublish-hvo/evidence/`
