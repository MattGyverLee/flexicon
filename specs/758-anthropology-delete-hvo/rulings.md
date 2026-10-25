# Issue #758 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #758 (P2) -- AnthropologyOperations Delete SubPossibilitiesOS/PossibilitiesOS HVO membership  
**Parent triage:** #756 LocationOperations Delete HVO family (out-of-scope anthropology delete paths)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#758** (filed this run; sibling gap after #756)

Untrusted open issues ignored per automation policy (#635 from rulingAnts).

## RULING (binding)

1. In `Delete`, locate the collection member whose `Hvo` matches the resolved
   item before calling `Remove` on `PossibilitiesOS` or `SubPossibilitiesOS`.
2. Do not rely on `Contains(item)` or pass the caller's bare handle directly
   to `Remove` without an HVO scan.
3. Tag the lookup with `issue #758` in comments.
4. Do not refactor unrelated AnthropologyOperations paths in this PR.

**Out of scope:** SemanticDomainOperations nested delete paths (next sibling gap).

## Verification plan

- Offline: `tests/operations/test_issue758_anthropology_delete_hvo_offline.py`
- Live: `tests/operations/test_issue758_anthropology_delete_hvo_live.py`
- Evidence: `specs/758-anthropology-delete-hvo/evidence/`
