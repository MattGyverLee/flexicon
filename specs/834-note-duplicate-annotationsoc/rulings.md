# Issue #834 -- lex-lead ruling

**Date:** 2026-11-02  
**Issue:** #834 (P2) -- NoteOperations.Duplicate insert_after silently ignored for AnnotationsOC owners  
**Parent triage:** #658 NoteOperations Duplicate HVO (ResponsesOS path fixed)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#834** (MattGyverLee; #833/#836 have open PRs #837/#838)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. **Option (a)** from the issue body: do not pretend `insert_after` works on unordered
   `AnnotationsOC` owners. Keep append-at-end behaviour; emit **`logger.warning`**
   when `insert_after=True` is requested on those paths.
2. Warn in **`__AttachReply`** when the scripture `ResponsesOS` path is unavailable and
   the reply is attached via `LangProject.AnnotationsOC` with `insert_after=True`.
3. Warn in **`Duplicate`** when the source owner exposes only `AnnotationsOC` (not
   `ResponsesOS`) and `insert_after=True`.
4. Correct the **`Duplicate` docstring**: `insert_after=True` preserves position only
   for ordered **`ResponsesOS`** owners; `AnnotationsOC` is unordered.
5. Tag warning sites with **`issue #834`** in comments.
6. Do not refactor unrelated NoteOperations paths in this PR.

**Out of scope:** Deriving display order for general discussion replies (issue option b).

## Verification plan

- Offline: `tests/operations/test_issue834_note_duplicate_annotationsoc_offline.py`
- Live: extend `tests/operations/test_issue658_note_duplicate_hvo_live.py` gate only if
  needed; behaviour unchanged except warning (membership assertions remain).
- Evidence: `specs/834-note-duplicate-annotationsoc/evidence/live-834.md`
