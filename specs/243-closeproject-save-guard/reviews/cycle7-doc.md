# Doc Agent Report

**Date:** 2026-09-07
**Trigger:** cycle-7 adjudication record for issue #243 (T8a/T8b/T7 recut, C20's ruling)

## What was written, and where

- `specs/243-closeproject-save-guard/spec.md` -- header bumped C1-C19 ->
  C1-C23; appended **C21** (blanket `CurrentDepth > 0` guard, mode-split
  message, Q4 rejected, P-11 caveat, three docstring corrections routed to
  T8b), **C22** (11-site test blast-radius table, public-API vs
  liblcm-mechanism split, `test_transaction_honesty.py:73` collateral), and
  **C23** (T7's `FP_ProjectError` raise withdrawn; ERROR log is the whole
  remedy; points 2/5 struck, 1/3/4 reworded).
- `specs/243-closeproject-save-guard/tasks.md` -- added T8a (DONE) and T8b
  (IN PROGRESS) under new **Checkpoint 2d (CP-D)**; rewrote T7 in place per
  C23 (unblocked, resequenced after T8b); narrowed T5b (docstring
  corrections moved out to T8b; kept CHANGELOG note, `docs/TRANSACTION_GUIDE.md`
  `:154-183`/`:43-50`/`:170-176`, Q4, and a new CHANGELOG-classification
  instruction for the exception-type change).
- `specs/tier1-silent-data-loss/QUEUE.md` -- added one "Awaiting user
  approval" entry: audit of the schema/metadata-mutating and
  exclusivity-sensitive operation class for depth-guard coverage, citing
  domain Q1/Q2/Q3 and the #250 overlap.

## C22 caveat (read before trusting the table)

My dispatch did not include the literal 11-site table `/lex-lead` is said
to have enumerated elsewhere. I reconstructed it independently by grepping
every `SaveChanges()` call site under `tests/` and reading each in place;
it confirms all three named details (probe `:658`, `TestSaveChangesIsUnusableInThisMode`,
`test_transaction_honesty.py:73`) and totals 11. Flagged in C22 itself as
"reconstructed, not copied" -- verify against your own enumeration.

## Frozen/out-of-scope text now contradicting, NOT edited

- `tasks.md`'s top "STATE AS OF SPURT 5" summary (~line 25-36) still says
  "T7 (BLOCKED on the user's coupled ruling)" -- stale post-C20/C23.
- `QUEUE.md` item 1's "STATUS ... needs_human" block and Campaign Log have
  no spurt 6/7 entries and still read as blocked.
- `QUEUE.md`'s existing `SaveChanges()` "Awaiting user approval" item is now
  largely superseded by C20/T8a/T8b but was left untouched (only one new
  entry was authorized).

No `flexicon/` or `tests/` file touched. No issues filed.

---
**Doc Agent:** /lex-doc
