# Issue #323 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/323-note-replies from origin/main

## RULING (binding)

`liblcm_baseline.json` and live T2.5 agree: **`ICmBaseAnnotation` has no
`RepliesOS`**. `IScrScriptureNote` exposes **`ResponsesOS`** for discussion
threads on scripture notes.

**Correct behaviour (issue #323 scope):**

1. **General annotations (`ICmBaseAnnotation`)** -- Model replies as separate
   annotations in `LangProject.AnnotationsOC` with `BeginObjectRA` pointing at
   the parent note. Discover direct replies by scanning the annotation
   repository for `BeginObjectRA.Hvo == parent.Hvo` (not `RepliesOS`).
2. **Scripture notes (`IScrScriptureNote`)** -- Use `ResponsesOS` for attach,
   detach, ordered insert, and iteration (same ordering semantics the old
   `RepliesOS` branch assumed).
3. **`annotation.py` wrapper** -- Mirror the same two-path reply discovery for
   `replies` / `has_replies`; do not guard on phantom `RepliesOS`.

**Out of scope:** Redesigning `GetAll()` filtering, scripture-only APIs, or
sync payload shape for note threads.

## Verification plan

- Offline: source ratchets on `NoteOperations` / `annotation.py` (no
  `RepliesOS` guards on `ICmBaseAnnotation` paths); unit tests for
  `__IterDirectReplies` / attach helpers with mocks.
- Live: read/write reply round-trip on `target_sandbox` when LCM is available
  (`requires_live_project`).
