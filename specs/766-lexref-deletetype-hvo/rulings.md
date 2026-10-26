# Issue #766 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #766 (P2) -- LexReferenceOperations DeleteType HVO membership  
**Parent triage:** #764 lex-lead ruling out-of-scope note (LexReference ref-type Delete sibling gap)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#766** (filed this run; DeleteType path)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `DeleteType`, locate the `ReferencesOA.PossibilitiesOS` member whose `Hvo`
   matches the resolved ref type before calling `Remove`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag lookups with `issue #766` in comments.
4. Do not refactor unrelated LexReferenceOperations paths in this PR.

**Out of scope:** Other PossibilitiesOS.Remove sites not listed in this ruling.

## Verification plan

- Offline: `tests/operations/test_issue766_lexref_deletetype_hvo_offline.py`
- Live: `tests/operations/test_issue766_lexref_deletetype_hvo_live.py`
- Evidence: `specs/766-lexref-deletetype-hvo/evidence/`
