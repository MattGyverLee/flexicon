# Issue #470 -- lex-lead ruling

**Date:** 2026-09-25  
**HEAD:** fix/470-reorder-clear from origin/main

## RULING (binding)

1. **LCM semantics:** On an LCM owning sequence, `Clear()` deletes every owned
   child (and subtree). Reordering via `Clear()` then `Add()` is P0 data loss
   (#470). The correct idiom is in-place `MoveTo`, as `BaseOperations.Sort`
   and the move helpers already use.

2. **Shared helper:** Add `BaseOperations._ApplySequenceOrder(sequence,
   desired_order)` -- full membership, `MoveTo` only, no `Clear()`. All five
   `Reorder()` implementations call it inside their existing transaction.

3. **LexSense partial reorder:** Docstring promises senses not in `sense_list`
   stay at the end in original order. Build
   `desired_order = resolved_senses + tail` before `_ApplySequenceOrder` (fixes
   the prior bug where `Clear()` dropped unlisted senses entirely).

4. **Pronunciation HVO path:** Resolve list members through
   `__GetPronunciationObject` before reorder (parity with other Reorder methods).

5. **Scope:** The five sites from the issue sweep only. Do not refactor
   `Sort()` or unrelated `Clear()` uses in this PR.

## Verification plan

- Offline: unit test for `_ApplySequenceOrder` on a mock sequence that fails
  if `Clear()` is called; AST ratchet forbids `.Clear()` inside each `Reorder`
  body in the five modules.
- Live: on `target_sandbox`, reorder a sequence with descendant data, re-read
  member GUIDs from the LCM (`FLEXLIBS_REQUIRE_LIVE=1`; cloud agent:
  **FAIL: unverified**).
