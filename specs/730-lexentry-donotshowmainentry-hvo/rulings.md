# Issue #730 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #730 (P2) -- LexEntryOperations AddDoNotShowMainEntryIn / RemoveDoNotShowMainEntryIn DoNotShowMainEntryInRC HVO membership  
**Parent triage:** #728 LexEntry DoNotPublishInRC fix explicitly left DoNotShowMainEntryInRC out of scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **none** on file at scan time; **#730** filed this run (LexEntry DoNotShowMainEntryInRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddDoNotShowMainEntryIn`, treat a publication as already linked when any member of `entry.DoNotShowMainEntryInRC` shares `publication.Hvo`, not `publication in DoNotShowMainEntryInRC`.
2. In `RemoveDoNotShowMainEntryIn`, locate the reference-collection member by matching `Hvo`, then call `Remove` on that member.
3. Tag both lookups with `issue #730` in comments.
4. Do not refactor unrelated LexEntry RC membership sites in this PR.

**Out of scope:** ExampleOperations DoNotPublishInRC, LexReference TargetsRS, Overlay PossItemsRC, and other RC HVO gaps not yet filed.

## Verification plan

- Offline: `tests/operations/test_issue730_lexentry_donotshowmainentry_hvo_offline.py`
- Live: `tests/operations/test_issue730_lexentry_donotshowmainentry_hvo_live.py`
- Evidence: `specs/730-lexentry-donotshowmainentry-hvo/evidence/`
