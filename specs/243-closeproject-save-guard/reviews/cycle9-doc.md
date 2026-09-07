# Cycle 9 -- Doc Agent: C28/C29 recorded, QUEUE.md updated, C27 staleness sweep

**Docs-only, live-exempt. Scope fence honoured: no `flexicon/`, `tests/`,
`CHANGELOG.md`, or `docs/` edits.**

## What landed

1. **`spec.md`** -- added **C28** (the `SaveChanges()` fail-open catch:
   breadth accepted, catch NOT narrowed, C21's policy NOT reopened;
   documented contract broadened via T9a, coverage added via T9b; residual
   named not resolved; P-11 prediction-before-measurement ruled NO ACTION
   with a forward rule for future tasks; the lex-qc/lex-verification gate
   substitution recorded) and **C29** (the `transaction.py:146-153`
   counter-measurement: protected as a true record like C10, given its own
   queue bullet rather than folded into C25, discriminating variables
   named). Header bumped C1-C27 -> C1-C29.
2. **`tasks.md`** -- header bumped to C1-C29, T7/T5b marked landed, new
   **Checkpoint CP-CLOSE** section added with **T9a** (docs/comment
   broadening) and **T9b** (offline test for the fail-open branch), both
   unchecked pending the parallel programmer dispatch.
3. **`STATUS.md`** -- "Last updated" and status banner bumped to spurt 9;
   spurt 6-8 section heading extended to "spurts 6-9"; new cycle-9
   paragraph added; "Contract decisions now frozen" list extended with
   C28/C29; "Next pickup" rewritten around T9; "Routed to the user"
   section gained C29's paragraph.
4. **`specs/tier1-silent-data-loss/QUEUE.md`** -- item-1 table cell updated
   (T7/T5b landed, QC gate result, T9 remaining); two new bullets added
   under "Awaiting user approval" (the C29 counter-measurement, and the
   `docs/TRANSACTION_GUIDE.md` gap), both gated behind the same
   unresolved question as the existing C25/P-11 bullet, which is preserved
   verbatim with its 25/25 pin intact.

## Verification before writing

Read `FLExProject.py:782-886` (`SaveChanges()`) directly: confirmed the
`except Exception as e:` fail-open catch at line 845 and its comment
scoping to "an unreadable depth." Read `transaction.py:130-163`: confirmed
the `set_RollBack`/`Dispose()` block and its inline comment recording the
live POS-vanished measurement at lines ~146-153. Read `reviews/cycle8-qc.md`
and `reviews/cycle8-programmer.md` for exact finding wording before
drafting C28/C29. No `flexicon/`, `tests/`, `docs/`, or `CHANGELOG.md`
files were touched.

## Not done (out of my scope)

`.crew-handoff.json` untouched per C27's explicit carve-out. No GitHub
issues filed. T9a/T9b implementation is `/lex-programmer`'s parallel task,
not mine.
