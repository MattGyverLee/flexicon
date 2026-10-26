# Issue #768 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #768 (P2) -- VariantOperations Delete EntryRefsOS HVO membership  
**Parent triage:** #597 lex-lead ruling out-of-scope note (Variant Delete sibling gap)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#768** (filed this run; Delete path)

Untrusted open issues ignored per automation policy (#635 from rulingAnts).

## RULING (binding)

1. In `Delete`, locate the `EntryRefsOS` member whose `Hvo` matches the
   resolved variant before calling `Remove`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag lookups with `issue #768` in comments.
4. Do not refactor unrelated VariantOperations paths in this PR.

**Out of scope:** Other EntryRefsOS mutators already covered (#597 Duplicate).

## Verification plan

- Offline: `tests/operations/test_issue768_variant_delete_hvo_offline.py`
- Live: `tests/operations/test_issue768_variant_delete_hvo_live.py`
- Evidence: `specs/768-variant-delete-hvo/evidence/`
