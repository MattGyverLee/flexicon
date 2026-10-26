# Issue #728 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #728 (P2) -- LexEntryOperations AddDoNotPublishIn / RemoveDoNotPublishIn DoNotPublishInRC HVO membership  
**Parent triage:** #726 LexSense DoNotPublishInRC fix explicitly left LexEntry out of scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#728** filed this run (LexEntry DoNotPublishInRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddDoNotPublishIn`, treat a publication as already linked when any member of `entry.DoNotPublishInRC` shares `publication.Hvo`, not `publication in DoNotPublishInRC`.
2. In `RemoveDoNotPublishIn`, locate the reference-collection member by matching `Hvo`, then call `Remove` on that member.
3. Tag both lookups with `issue #728` in comments.
4. Do not refactor unrelated LexEntry RC membership sites in this PR.

**Out of scope:** `AddDoNotShowMainEntryIn` / `RemoveDoNotShowMainEntryIn`, ExampleOperations DoNotPublishInRC, and LexSense RC HVO gaps with open PRs (#718–#726).

## Verification plan

- Offline: `tests/operations/test_issue728_lexentry_donotpublish_hvo_offline.py`
- Live: `tests/operations/test_issue728_lexentry_donotpublish_hvo_live.py`
- Evidence: `specs/728-lexentry-donotpublish-hvo/evidence/`
