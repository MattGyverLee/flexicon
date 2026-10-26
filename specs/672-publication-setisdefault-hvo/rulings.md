# Issue #672 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #672 (P2) -- PublicationOperations SetIsDefault PossibilitiesOS index  
**Parent triage:** #597 VariantOperations; #652 LocationOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#640 P1 has PR #641)
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#672** filed this run (PublicationOperations sibling gap)

## RULING (binding)

1. In `SetIsDefault`, locate the publication in `PublicationTypesOA.PossibilitiesOS`
   by comparing each member's `Hvo` to `publication.Hvo`, not `in` / `IndexOf`
   on the resolved object reference.
2. If no member matches, return without reordering (preserve prior no-op when
   the publication is not in the list).
3. Tag the lookup with `issue #672` in comments.
4. Do not refactor unrelated PublicationOperations paths in this PR.

**Out of scope:** Other `IndexOf` / sequence membership sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue672_publication_setisdefault_hvo_offline.py`
- Live: `tests/operations/test_issue672_publication_setisdefault_hvo_live.py`
- Evidence: `specs/672-publication-setisdefault-hvo/evidence/`
