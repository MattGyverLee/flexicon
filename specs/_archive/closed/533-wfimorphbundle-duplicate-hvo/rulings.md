# Issue #533 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #533 (P2) -- WfiMorphBundleOperations Duplicate insert_after MorphBundlesOS index  
**Parent triage:** #531 ParagraphOperations Duplicate HVO; #528 ReplaceAnalysis HVO (this site was out of scope there)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#533** this run; #527 has open PR #530)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source bundle in
   `parent.MorphBundlesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `list(...).index(source)`.
2. If no member matches, keep the existing fallback: insert at
   `len(bundle_list)` (append).
3. Tag the lookup with `issue #533` in comments.
4. Do not refactor unrelated WfiMorphBundleOperations paths in this PR.

**Out of scope:** `NaturalClassOperations.Duplicate` `.index(source)`; ParagraphOperations #531 (merged).

## Verification plan

- Offline: `tests/operations/test_issue533_wfimorphbundle_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue533_wfimorphbundle_duplicate_hvo_live.py`
- Evidence: `specs/533-wfimorphbundle-duplicate-hvo/evidence/`
