# Domain Expert Review — flexicon#243 P1: public read of LCM task depth

**Date:** 2026-09-07
**Domain:** FLEx/LCM write-path transaction plumbing
**Status:** Options paper (analysis only, no implementation)

## Q1 — Name and shape

**Options:** (a) `HasOpenSessionTask() -> bool` only; (b) `CurrentDepth` int passthrough only; (c) both.

**Recommendation: both, with `HasOpenSessionTask()` scoped narrowly to the `undoable=False` envelope question, unconditionally `False` under `undoable=True`.**

`HasOpenSessionTask()` should not try to be a mode-agnostic "is anything open" predicate — that question has no single honest answer, since depth=1 means two structurally different things per mode (existing docstring at FLExProject.py:664-679 already draws this line for `AbortSession`). Instead, define it as answering exactly the P1 problem statement: "is the session-long `BeginNonUndoableTask()` envelope currently open?" In `undoable=True` that envelope never exists by construction, so the honest, non-raising answer is always `False` — this is not "nothing to report," it is a correct and useful fact (callers in that mode should never be asking this question in the first place; `False` tells them so). `CurrentDepth` is kept as a raw int passthrough alongside it for the diagnostic/undoable=True case, where the caller genuinely needs the raw depth (mirroring the three existing internal call sites).

## Q2 — Return contract at the edges

**writeEnabled=False:** return the real value, do not raise. No envelope is ever opened for a read-only project (guard at FLExProject.py:282 requires `writeEnabled`), so `CurrentDepth` is legitimately 0 and `HasOpenSessionTask()` legitimately `False`. Unlike `AbortSession`/`SaveChanges`, this is a pure read with no mutating consequence, so `FP_ReadOnlyError` would be domain-wrong here — it signals "you tried to write," not "you tried to look."

**After CloseProject() / never opened:** raise, not return a value. Both states are indistinguishable — `self.project` does not exist (`del self.project` at line 335; never set before `OpenProject`). Returning a silent `0`/`False` here is precisely the failure mode P1 exists to prevent: a caller silently getting a wrong answer instead of the exception that tells it the session is unusable. Raise `FP_ProjectError` ("project is not open"), reusing the existing lifecycle exception rather than inventing a new one — there is no `FP_ProjectNotOpenError` in `exceptions.py`, and every other method on this class currently gets this for free via `AttributeError` on `self.project`; a real exception here is strictly better, not a new pattern.

## Q3 — Expose the raw int?

**Yes, expose `CurrentDepth`.** The CLAUDE.md hiding rule targets *structural* LCM complexity (interface casting, `ClassName` branching) where hiding adds real value. `CurrentDepth` is a scalar diagnostic already reasoned about in prose in `AbortSession`'s own docstring (lines 684-692) and already read via `getattr(..., 0)` at three call sites (transaction.py:172, undoable_operation.py:102, CustomFieldOperations.py:306) — it is de facto already a documented escape hatch, same tier as `.Cache`. Document its mode-dependent meaning explicitly and point callers at `HasOpenSessionTask()` for the common `undoable=False` question so most callers never need to interpret the int themselves.

## Q4 — De-duplication

**Consolidate the depth *read* into one private helper; do not inherit the lenient fallback into the public surface.** All four sites should share one line — "read `action_handler.CurrentDepth` off a live LCM action handler" — but the three internal callers' `except: return 0`/`getattr(..., 0)` exists to tolerate incomplete test doubles, not to describe real LCM behavior. The new public property/method must check "is the project actually open" itself (Q2) and raise there; only once past that guard should it call the shared lenient depth-read. Consolidating naively would make the public API silently return 0 for a closed/never-opened project, reintroducing the exact ambiguity P1 is meant to remove.

## Q5 — Dependency on P0 (CloseProject ordering guard)

**P1 should land with or before P0, and P0 should consume it.** `CloseProject()` (FLExProject.py:322-338) unconditionally calls `EndNonUndoableTask()` whenever `writeEnabled and not self._undoable`, with no check that an envelope is actually open — exactly the "opposite corruption" case in the prompt: if a prior `AbortSession()` rollback succeeded but its envelope reopen failed (the `FP_ProjectError` path at lines 790-796), `CloseProject()` will still try to End a task that was never reopened. P0's guard should call the depth read (`HasOpenSessionTask()`, or `CurrentDepth > 0`) before calling `EndNonUndoableTask()`, skipping it with a debug log when no envelope is open, rather than assuming the mode implies the envelope's presence.

---
**Reviewed By:** Domain Expert Agent
**Files consulted:** `flexicon\code\FLExProject.py` (164-338, 563-588, 637-800), `flexicon\code\transaction.py` (40-110, 172-189), `flexicon\code\undoable_operation.py` (90-119), `flexicon\code\System\CustomFieldOperations.py` (280-333), `flexicon\code\exceptions.py`
