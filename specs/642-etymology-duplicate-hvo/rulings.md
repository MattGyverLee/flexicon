# Issue #642 -- lex-lead ruling

**Date:** 2026-10-22  
**Issue:** #642 (P2) -- EtymologyOperations Duplicate insert_after EtymologyOS index  
**Parent triage:** #597 VariantOperations; #550 LexSense Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#642** filed this run (EtymologyOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source etymology in
   `parent.EtymologyOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `EtymologyOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #642` in comments.
4. Do not refactor unrelated EtymologyOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue642_etymology_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue642_etymology_duplicate_hvo_live.py`
- Evidence: `specs/642-etymology-duplicate-hvo/evidence/`
