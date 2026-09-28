# Cycle 2 — Doc Agent report (task MCP)

**Deliverable:** `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`, written.

## Definitively answered (all six)

1. **Raw-LCM/`run_module`** — join-not-nest via `DoUsingNewOrCurrentUOW`
   (F3), with F1's Rollback(0)-then-throw made bold and explicit as the
   data-loss reason join is load-bearing.
2. **Save cadence** — F4 mechanics + Q1's linguist-facing framing (silent
   hang, then bulk flush; total loss on mid-run crash under
   `undoable=False`) both included with a 4.3.0-vs-post-Track-B table.
3. **`CAPABILITIES`** — documented as PLANNED with the AttributeError
   demonstrated and the `getattr(..., frozenset())` snippet given verbatim.
   Flagged (not silently assumed) that no task ID currently tracks it.
4. **Nesting** — P1/P2 coverage counts, the three real decorated→decorated
   pairs, and the one-sentence memorable rule, all sourced.
5. **`ILcmUI`/#238/#236** — canonical `FP_ConflictingSaveError` import
   documented per the P0 fix, back-compat import confirmed, rollback bluntly
   stated as session-wide-only via `Rollback(0)`, Q4's full-stop-not-retry
   guidance carried verbatim.
6. **`CreateField`** — revised draft's corrected chain, F6's refutation of
   the guard's *rationale* (not the guard), the bold Track-B-doesn't-imply-
   implementation correction, and the `FieldDescription.UpdateCustomField`
   implementation path with line citations.

## Blocked on NOT FOUND IN SOURCE

- `IActionHandler`'s full contract (F5(a)) — flagged as unknown, not
  guessed at, in the rollback table.
- O3 (`DiscardToMark` semantics) — not directly needed by the six questions
  but noted implicitly via not building rollback claims on it.

## Crew disagreements surfaced (not resolved)

- `RefreshFromDisk()` writeEnabled guard: domain (approve) vs QC (forecloses
  a plausible read-only monitoring caller) — presented as unresolved.
- B2 shape: central dispatch bracket (lex-lead's provisional call) vs the
  dispatch-layer probe's findings (100% validator regression, 29% label
  loss, hybrid's own weak point) — marked OPEN, flagged as blocking B2's
  ship timeline.

## Gaps flagged for the crew (new, found during this pass)

- No task ID exists yet for `flexicon.CAPABILITIES`, for enforcing D3 as a
  precondition, or for `CreateField`'s actual schema-mutation implementation.
  All three recommended for filing in `tasks.md`.

Test-suite state reported per the p0-fix re-verification (1638/139/20/17,
tests/contract excluded) — not described as green anywhere in the contract.

---
**Doc Agent:** /lex-doc
