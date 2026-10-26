# Issue #744 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #744 (P2) -- LexReferenceOperations GetComplexFormEntries / GetComponentEntries dedupe  
**Parent triage:** #742 RemoveTarget TargetsRS HVO family (PR #743 in flight)

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#640 has #641)
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#744** filed this run (LexReference read-path dedupe sibling gap)

## RULING (binding)

1. In `GetComplexFormEntries` and `GetComponentEntries`, when collecting
   `other_target` entries from `TargetsRS`, skip append when any result list
   member already shares `other_target.Hvo` — do not use `other_target not in`
   on the Python list (proxy identity).
2. Tag each dedupe block with `issue #744` in comments.
3. Do not refactor `RemoveTarget` or other LexReference paths in this PR
   (#742 owns RemoveTarget).

**Out of scope:** `AddTarget`, sync `targets_rs` rewrite, other Operations HVO backlog.

## Verification plan

- Offline: `tests/operations/test_issue744_lexreference_complex_entries_hvo_offline.py`
- Live: `tests/operations/test_issue744_lexreference_complex_entries_hvo_live.py`
- Evidence: `specs/744-lexreference-complex-entries-hvo/evidence/`
