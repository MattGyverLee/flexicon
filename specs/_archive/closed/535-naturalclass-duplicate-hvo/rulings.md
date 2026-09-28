# Issue #535 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #535 (P2) -- NaturalClassOperations Duplicate insert_after NaturalClassesOS index  
**Parent triage:** #533 WfiMorphBundle Duplicate (named this site out of scope); #531 ParagraphOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#535** this run; #533/#527 have open PRs #534/#530)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source natural class in
   `phon_data.NaturalClassesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `list(...).index(source)`.
2. If no member matches, keep the existing fallback: insert at
   `len(nc_list)` (append).
3. Tag the lookup with `issue #535` in comments.
4. Do not refactor unrelated NaturalClassOperations paths in this PR.

**Out of scope:** WfiMorphBundle #533 (PR #534); other HVO membership sites.

## Verification plan

- Offline: `tests/operations/test_issue535_naturalclass_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue535_naturalclass_duplicate_hvo_live.py`
- Evidence: `specs/535-naturalclass-duplicate-hvo/evidence/`
