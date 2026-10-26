# Issue #738 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #738 (P2) -- VariantOperations Add/RemoveComponentLexeme ComponentLexemesRS HVO membership  
**Parent triage:** #736 Overlay PossItemsRC / LexEntry AddComplexFormComponent HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **none on file** -- filed **#738** this run (VariantOperations sibling gap)

## RULING (binding)

1. In `AddComponentLexeme`, treat the entry as already present when any
   `ComponentLexemesRS` member shares its `Hvo`; do not rely on identity-only
   duplicate detection (and do not open an empty transaction for redundant adds).
2. In `RemoveComponentLexeme`, scan `ComponentLexemesRS` for the member whose
   `Hvo` matches, then call `Remove` with that collection member reference; if
   none match, no-op.
3. Tag both sites with `issue #738` in comments.
4. Do not refactor unrelated VariantOperations paths in this PR.

**Out of scope:** MSA `ProdRestrictRC` exception features; Allomorph `PhoneEnvRC` /
`InflectionClassesRC`; LexEntry complex-form RS (already HVO-safe).

## Verification plan

- Offline: `tests/operations/test_issue738_variant_componentlexeme_hvo_offline.py`
- Live: `tests/operations/test_issue738_variant_componentlexeme_hvo_live.py`
- Evidence: `specs/738-variant-componentlexeme-hvo/evidence/`
