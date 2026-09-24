# Issue #210 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/210-strict-transactions from origin/main

## RULING (binding)

PR #204 review (Domain Concern 2): Phase 1 `_FLExTransaction` with `(None, None)`
mark/rollback must stay **warn-and-continue by default** so `undoable=False` write
sessions remain usable while liblcm exposes no rollback-to-mark API (issue #236).

Callers who require **fail-fast** when no rollback API is wired may opt in.

**Correct behaviour (issue #210 scope):**

1. Add `strict_transactions: bool = False` to `FLExProject.OpenProject()`. Store
   on the instance as `_strict_transactions` (meaningful only when
   `writeEnabled=True`; otherwise forced False).
2. In `_FLExTransaction.__enter__`, when `writeEnabled`, `mark_fn is None`, and
   `getattr(project, "_strict_transactions", False)`, raise `FP_TransactionError`
   with a message naming `strict_transactions=True`, the absent rollback API, and
   the remedies (`undoable=True` default, or reopen with
   `strict_transactions=False`).
3. **Default unchanged:** `_strict_transactions` False -> enter proceeds with no
   rollback (current behaviour). The one-shot `OpenProject()` warning for
   explicit `undoable=False` stays as-is.
4. **Read-only:** no strict check (writes fail at validation anyway).

**Out of scope:** Discovering or wiring a real Mark/RollbackToMark API (#236 /
`docs/RESEARCH_NEEDED.md`); changing `_NestingAwareTransaction` Phase 2 paths;
live LCM proof on this cron run.

## Verification plan

- Offline: extend `tests/operations/test_transaction_rollback.py` for strict
  raise vs default enter; source ratchet that `OpenProject` accepts
  `strict_transactions`.
- Live: N/A for this flag plumbing (no LCM API change). Cloud agent:
  **FAIL: unverified** if SIL.LCModel unavailable -- acceptable for opt-in guard
  only.
