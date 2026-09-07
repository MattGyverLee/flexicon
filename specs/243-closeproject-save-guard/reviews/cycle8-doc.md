# Doc Agent Report -- cycle 8

**Date:** 2026-09-07
**Trigger:** dispatch from `/lex-lead` (spurt 8) -- CHANGELOG correction
(C24), `docs/TRANSACTION_GUIDE.md` fixes (T5b), record C24-C27, QUEUE.md
updates, staleness sweep. Docs-only, live-exempt.

## Manifest entries reviewed

No `docs/MANIFEST.md` exists in this repo; worked directly from the
dispatch's file list (CHANGELOG.md, docs/TRANSACTION_GUIDE.md, spec.md,
tasks.md, STATUS.md, QUEUE.md) per instruction.

## Part 1 -- CHANGELOG.md (C24)

- New `### Changed` bullet: `SaveChanges()`'s exception-type change
  (liblcm `InvalidOperationException` -> `FP_TransactionError`), per-mode
  remedy, cross-referenced to `[4.4.0]`'s `undoable` default-flip entry.
- `### Fixed` paragraph (old `:82`) replaced with the two-step chain and
  the 25/25 re-measurement, plus a two-carve-out anti-overclaim clause
  (C10 `.fwdata`; single-client-only).
- Added a fourth paragraph for T7 (landing in parallel this cycle),
  explicitly flagged for `/lex-lead` to verify against the landed diff.

## Part 2 -- docs/TRANSACTION_GUIDE.md (T5b)

- 10-line accuracy banner added, citing
  `test_transaction_honesty.py::TestTransactionHonesty::test_transaction_runs_body_and_reraises_without_rollback`
  and the "no LCM rollback API found" path. Assertion only, no rewrite.
- Both `SaveChanges()` usage examples (`:43-50`, `:170-176` pre-edit) given
  a mode note stating the `undoable=False` refusal.
- The "No side effects on transactions" bullet inverted to the measured
  contract (C21), with the pre-guard collapse/discard mechanism named.
- Q4 CLOSED in `spec.md`: amend `[Unreleased]` in place, cross-reference
  `[4.4.0]` by prose, one-paragraph rationale recorded.
- C25 discipline honoured: no claim that an escaping exception safely
  discards work; no generalisation of the 25/25 creation-survival finding
  to property mods/deletions; `undoable_operation.py`/`transaction.py`
  untouched.

## Part 3 -- spec.md: C24-C27 recorded, header bumped to C1-C27

Added C24 (CHANGELOG correction), C25 (P-11 routing), C26 (C22 table
re-keyed to `/lex-lead`'s 11-item enumeration, three previously-unlisted
edits surfaced, "(and `:154`)" deleted, ADDENDUM item D on the
double-widened `test_transaction_honesty.py` slice, general rule
recorded), C27 (staleness-sweep ownership, explicitly excluding
`.crew-handoff.json`). One-line addendum added to C23 (route-1 now
measured; WARNING-downgrade considered and rejected).

## Part 4 -- QUEUE.md

- Row-1 status: `needs_human` -> `active`.
- "### 1." STATUS block rewritten current.
- Existing SaveChanges() "Awaiting user approval" item marked
  APPROVED/LANDED, kept (not deleted) as audit trail.
- New "Awaiting user approval" entry for C25 (rollback-discard audit).
- Campaign Log: added spurt 6, 7, 8 entries (previously absent).

## Part 5 -- staleness sweep performed

- `tasks.md`: "STATE AS OF SPURT 5" -> "SPURT 8" block rewritten; T8a/T8b
  marked DONE; T7/T5b marked IN PROGRESS; stale "Q2/Q4 remain open" line
  and a stray `:154` cross-reference corrected; T8b OUTCOME + CP-D
  REACHED note added.
- `spec.md`: READ THIS FIRST banner and Status block rewritten so C17's
  ceiling statement stays true while stating T8b met it; "needs_human"
  dropped; ralph-loop-cancelled statement kept; Q5's stale
  `needs_human`/blocker paragraph reframed as historical.
- `STATUS.md` (not explicitly named in the dispatch, done anyway per C27):
  top banner, spurt 6-8 summary, Q4/Q5 status, "Next pickup" and "Routed
  to the user" sections rewritten current.

## Findings NOT authorised to fix -- flagged for routing

- **`specs/243-closeproject-save-guard/.crew-handoff.json` is severely
  stale** (`status: needs_human`, `last_cycle: 5`, `blocker` field still
  describing the now-resolved C20 decision, `tasks_done` missing
  T8a/T8b). Per C27 (which I scoped to exclude this file -- it is
  machine orchestration state, not prose) this is `/lex-lead`'s or
  `/lex-archivist`'s to update, not mine. Flagging per the dispatch's
  explicit ask.
- `docs/TRANSACTION_GUIDE.md`'s API Reference section (`SaveChanges()`
  "Raises" list, near the bottom) still lists only `FP_ReadOnlyError`,
  omitting `FP_TransactionError`. Out of the bounded scope given ("Fix
  ONLY these"), left untouched, flagged here.
- `tasks.md`/`QUEUE.md` still carry several spurt-scoped historical
  paragraphs (e.g. "Resume from `.crew-handoff.json`... CP-B / T3") that
  read as live instructions if skimmed out of context; left as append-only
  history consistent with the rest of the file's style, not edited.

## Files touched

`CHANGELOG.md`, `docs/TRANSACTION_GUIDE.md`,
`specs/243-closeproject-save-guard/spec.md`,
`specs/243-closeproject-save-guard/tasks.md`,
`specs/243-closeproject-save-guard/STATUS.md`,
`specs/tier1-silent-data-loss/QUEUE.md`.

No file under `flexicon/` or `tests/` touched.

---
**Doc Agent:** /lex-doc
