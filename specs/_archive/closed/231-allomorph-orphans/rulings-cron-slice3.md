# Issue #231 -- lex-lead ruling (cron slice 3)

**Date:** 2026-09-24  
**HEAD:** `fix/231-remove-orphaned-live-slice3` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#441 fix on `main`; close-out
  draft PR #444 is docs-only and counts as in-flight for #441)
- Open **P2** bugs without an open PR: **#231** (slices 1--2 merged via #427,
  #439; no open PR)
- Did not select P3 #268 (lower priority while P2 is open)

## RULING (binding)

Slices 1--2 shipped mock coverage and production logic for duplicate-lexeme and
invalid-stale purges. **This PR adds live LCM verification** that the
duplicate-lexeme path reaches the database and that ``entry=`` accepts a genuine
``int`` HVO.

1. Add ``tests/operations/test_issue231_allomorph_remove_orphaned_live.py`` on
   ``target_sandbox`` only:
   - Create ``TEST_231_*`` entry with lexeme form and one real alternate.
   - Inject the lexeme into ``AlternateFormsOS`` again (promotion artifact shape).
   - Call ``RemoveOrphaned(entry=entry_hvo)`` with ``isinstance(entry_hvo, int)``.
   - Assert ``duplicate_lexeme`` in ``result.removed`` and **re-query the entry
     by HVO** -- lexeme must remain on ``LexemeFormOA`` and must not appear in
     ``AlternateFormsOS``; the non-duplicate alternate is kept.
2. Extend mock tests with **progress callback** parity (MSA ``RemoveOrphaned``
   precedent): per-entry invocation count and swallowed callback exceptions.
3. Offline ratchet: ``tests/operations/test_issue231_allomorph_remove_orphaned_offline.py``.

**Out of scope:** MorphRA-aware unused-allomorph sweeps, example/translation orphans,
feature-structure orphans, claiming full closure of #231.

## Verification plan

- Offline:
  ``python -m pytest tests/operations/test_issue231_allomorph_remove_orphaned.py tests/operations/test_issue231_allomorph_remove_orphaned_offline.py -q``
- Live (FieldWorks):
  ``FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue231_allomorph_remove_orphaned_live.py -m requires_live_project -q``
- Evidence: ``specs/231-allomorph-orphans/evidence/offline-231-slice3.md``
