# Issue #656 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #656 (P2) -- SemanticDomainOperations Duplicate insert_after HVO index  
**Parent triage:** #642–#654 Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#656** filed this run (SemanticDomainOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source domain in
   `parent.SubPossibilitiesOS` or top-level `SemanticDomainListOA.PossibilitiesOS`
   by comparing each member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #656` in comments.
4. Do not refactor unrelated SemanticDomainOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue656_semanticdomain_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue656_semanticdomain_duplicate_hvo_live.py`
- Evidence: `specs/656-semanticdomain-duplicate-hvo/evidence/`
