# Issue #231 -- lex-lead ruling (cron slice 2)

**Date:** 2026-09-24  
**HEAD:** `fix/231-allomorph-invalid-stale` from `origin/main`

## Triage

- No open **P0** or **P1** bugs without an open PR.
- Selected **P2 #231** (only P2 bug open; slice 1 merged via PR #427; no open PR).

## RULING (binding for this PR)

Issue #231 tracks three orphan-cleanup families. Slice 1 (duplicate lexeme
form in ``AlternateFormsOS``) is on ``main``.

**This PR delivers slice 2 only:**

1. ``AllomorphOperations.RemoveOrphaned`` also removes **invalid stale**
   alternates: any ``AlternateFormsOS`` member with ``IsValidObject`` false
   is dropped from the owning list (reason ``invalid_stale``). This closes
   the slice-1 gap where invalid duplicate-lexeme slots were skipped and
   left in the list.
2. **Explicitly deferred (remain on #231):** ``IWfiMorphBundle.MorphRA``-aware
   sweeps for *valid* alternates with no interlinear link -- valid alternates
   are often intentional inventory, not orphans, until a confirmed back-ref set
   says otherwise (same bar as #206 / MSA ``RemoveOrphaned``).
3. **Still out of scope:** example-sentence / translation orphans and
   phonological feature-structure orphans.

## Verification plan

- Offline: extend ``tests/operations/test_issue231_allomorph_remove_orphaned.py``.
- Live LCM: **FAIL: unverified** on cloud agent (no FieldWorks / pythonnet).
