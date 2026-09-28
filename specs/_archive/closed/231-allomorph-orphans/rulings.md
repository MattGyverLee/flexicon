# Issue #231 -- lex-lead ruling (cron slice 1)

**Date:** 2026-09-24  
**HEAD:** `fix/231-allomorph-orphan-dupes` from `origin/main`

## Triage

- No open **P0** or **P1** bugs without an open PR (2026-09-24 cron).
- Selected **P2 #231** (no open PR; other P2 items already have cron PRs).

## RULING (binding for this PR)

Issue #231 tracks three orphan-cleanup families (unused alternates after
lexeme swap, orphaned examples/translations, orphaned feature values). Each
needs a confirmed back-ref set before a project-wide helper ships (same lesson
as #206 / MSA ``RemoveOrphaned``).

**This PR delivers slice 1 only:**

1. ``AllomorphOperations.RemoveOrphaned(entry=None, progress=None)`` removes
   **duplicate lexeme-form listings** from ``AlternateFormsOS``: an allomorph
   whose ``Hvo`` equals the owning entry's ``LexemeFormOA.Hvo`` is removed
   from the alternates list only (``LexemeFormOA`` is unchanged).
2. **Out of scope (remain on #231):** MorphRA-aware unused-allomorph sweeps,
   example/translation orphans, phonological feature-structure orphans, and
   filing per-type follow-up issues once lex-domain confirms each back-ref set.

## Verification plan

- Offline: mock sweep in ``tests/operations/test_issue231_allomorph_remove_orphaned.py``.
- Live LCM: **FAIL: unverified** on cloud agent (no FieldWorks / pythonnet).
