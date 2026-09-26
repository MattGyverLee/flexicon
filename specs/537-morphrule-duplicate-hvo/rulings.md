# Issue #537 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #537 (P2) -- MorphRuleOperations Duplicate insert_after CompoundRulesOS / AffixTemplatesOS index  
**Parent triage:** #535 NaturalClass Duplicate; #533 WfiMorphBundle; #531 ParagraphOperations HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#537** this run)

## RULING (binding)

1. In `__DuplicateCompoundRule` when `insert_after=True`, locate the source rule in
   `morph_data.CompoundRulesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `CompoundRulesOS.IndexOf(source)`.
2. In `__DuplicateAffixTemplate` when `insert_after=True`, locate the source template in
   `owner.AffixTemplatesOS` by HVO the same way, not `AffixTemplatesOS.IndexOf(source)`.
3. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
4. Tag both lookups with `issue #537` in comments.
5. Do not refactor unrelated MorphRuleOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue537_morphrule_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue537_morphrule_duplicate_hvo_live.py`
- Evidence: `specs/537-morphrule-duplicate-hvo/evidence/`
