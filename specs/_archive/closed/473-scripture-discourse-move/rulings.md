# Issue #473 -- lex-lead ruling

**Date:** 2026-09-25  
**HEAD:** fix/473-scripture-discourse-move from origin/main

## RULING (binding)

1. **Move semantics (cross-owner):** When re-parenting an ownee onto a
   *different* owning sequence (`ScrSection` across Scripture books,
   `IConstChartRow` across discourse charts), use a single
   `Insert(index, item)` on the destination. **Never**
   `Remove` then `Insert` -- `LcmOwningSequence.Remove` deletes the ownee
   and its subtree (P0, same class as #448/#471/#472).

2. **Same-owner reorder:** When the source and destination sequence are the
   same object, use `seq.MoveTo(i, i, seq, j)` only (mirror
   `ConstChartRowOperations.MoveTo` same-chart branch and
   `BaseOperations` move helpers). Do not `Remove` + `Insert` within one
   book/chart.

3. **Scope:** `ScrSectionOperations.MoveTo` and
   `ConstChartRowOperations.MoveTo` cross-chart branch only for this PR.
   `Reorder()` Clear+Add sites (#470) are out of scope.

## Verification plan

- Offline: AST ratchet forbids `.Remove(section)` / `.Remove(row)` inside
  the affected `MoveTo` bodies; mock test that cross-book/cross-chart
  paths call `Insert` without prior `Remove`.
- Live: on `target_sandbox`, move a section across books and a chart row
  across charts; re-read GUIDs from LCM (`FLEXLIBS_REQUIRE_LIVE=1`; cloud
  agent: **FAIL: unverified** if FLEx unavailable).
