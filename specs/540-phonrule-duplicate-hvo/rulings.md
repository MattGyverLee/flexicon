# Issue #540 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #540 (P2) -- PhonologicalRuleOperations Duplicate insert_after PhonRulesOS index  
**Parent triage:** #537 MorphRule Duplicate (named other sites out of scope); #535 NaturalClass Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#540** (filed this run; #537 closed at PR #538)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source rule in
   `phon_data.PhonRulesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `PhonRulesOS.IndexOf(source)`.
2. If no member matches, keep the existing fallback: insert at
   `len(rule_list)` (append).
3. Tag the lookup with `issue #540` in comments.
4. Do not refactor unrelated PhonologicalRuleOperations paths in this PR.

**Out of scope:** MorphRule #537 (merged); other HVO membership / Duplicate IndexOf sites.

## Verification plan

- Offline: `tests/operations/test_issue540_phonrule_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue540_phonrule_duplicate_hvo_live.py`
- Evidence: `specs/540-phonrule-duplicate-hvo/evidence/`
