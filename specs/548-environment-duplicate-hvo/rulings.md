# Issue #548 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #548 (P2) -- EnvironmentOperations Duplicate insert_after EnvironmentsOS index  
**Parent triage:** #540 PhonologicalRule Duplicate; #535 NaturalClass; #531 ParagraphOperations HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: enhancement gaps #542-547 only; filed **#548** this run (same-class Duplicate HVO defect)

## RULING (binding)

1. In `EnvironmentOperations.Duplicate` when `insert_after=True`, locate the source
   environment in `phon_data.EnvironmentsOS` by comparing each member's `Hvo` to
   `source.Hvo`, not `EnvironmentsOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #548` in comments.
4. Do not refactor unrelated EnvironmentOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes (e.g. POSOperations).

## Verification plan

- Offline: `tests/operations/test_issue548_environment_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue548_environment_duplicate_hvo_live.py`
- Evidence: `specs/548-environment-duplicate-hvo/evidence/`
