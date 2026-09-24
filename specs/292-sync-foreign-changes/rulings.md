# Issue #292 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/292-sync-foreign-changes from origin/main

## RULING (binding)

Mid-session ingestion of peer commits under `OpenProject(undoable=False)` requires
temporarily leaving the session-long non-undoable envelope so `IUndoStackManager.Save()`
can run at a legal depth (`ReadyForBeginTask`). `SaveChanges()` correctly refuses
that path (#243); `RefreshFromDisk()` clears reconciliation wedges but does not
drive the commit-log replay FlexToolsMCP #96 needs.

**Correct behaviour (issue #292 scope):**

1. Add `FLExProject.SyncForeignChanges()` as a named wrapper for:
   `EndNonUndoableTask()` (when `HasOpenSessionTask()`), `usm.Save()`,
   `BeginNonUndoableTask()` in a `finally` when an end occurred.
2. **Mode:** `undoable=False` only. Under `undoable=True`, refuse with
   `FP_TransactionError` pointing callers at `SaveChanges()` after blocks exit.
3. **Depth:** Require `CurrentDepth == 1`. At depth `0`, refuse and name
   `SaveChanges()`. At any other depth, refuse (unexpected FSM).
4. **Guards:** Refuse attached views (`FromOpenProject`) and read-only sessions,
   matching `SaveChanges()` / `AbortSession()` ownership rules.
5. **Failure:** If `BeginNonUndoableTask()` fails after a successful save,
   raise `FP_ProjectError` (session no longer writable; mirror `AbortSession()`).

**Out of scope:** Changing `SaveChanges()` depth policy, shared-mode detection,
live two-session proof (document as follow-up), or MCP-side wiring.

## Verification plan

- Offline: mock `MainCacheAccessor` / `ObjectRepository` sequence tests; source
  ratchet that the method exists and calls `End`/`Save`/`Begin`.
- Live: two write-enabled peers on a shared project (Windows FieldWorks). Cloud
  agent: **FAIL: unverified** if SIL.LCModel is unavailable.
