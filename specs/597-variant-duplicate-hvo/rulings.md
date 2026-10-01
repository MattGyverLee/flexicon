# Issue #597 -- lex-lead ruling

**Date:** 2026-09-29  
**Issue:** #597 (P2) -- VariantOperations Duplicate insert_after EntryRefsOS index  
**Parent triage:** #552 ExampleOperations; #550 LexSense Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#597** filed this run (VariantOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source variant in
   `parent.EntryRefsOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `EntryRefsOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #597` in comments.
4. Do not refactor unrelated VariantOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue597_variant_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue597_variant_duplicate_hvo_live.py`
- Evidence: `specs/597-variant-duplicate-hvo/evidence/`
