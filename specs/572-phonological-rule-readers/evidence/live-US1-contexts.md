# Live evidence -- US1 contexts (T008, issue #572)

**Worktree:** `C:/Github/flexicon-572`, branch `fix/572-phonological-rule-readers`.
**Date:** 2026-09-28
**Nature:** `morphboundary` opened read-only throughout. The only writes are
three `TEST_572_US1_*` contexts on the real Target, removed in a `finally:`.

## Exact commands

```powershell
cd C:\Github\flexicon-572
python -m pytest tests/test_context_wrappers.py -q
# 26 passed in 0.77s

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_context_readers_live.py -m requires_live_project -q
# 5 passed in 4.32s
```

## LIVE GATE

`tests/live_status.json`, read immediately after the live run:

```json
"run_mode": "live"
```

FieldWorks 9 `SIL.LCModel` loaded; this was a live run, not a mock fallback.

## Pass/fail lines

- `tests/test_context_wrappers.py`: **26 passed** (was 23 passed + 3 failed
  before T005-T007; the 3 failures were the boundary-filter tests failing
  against the old `by_type("PhBoundaryContext")`).
- `tests/operations/test_issue572_context_readers_live.py`: **5 passed**
  (4 read-only on `morphboundary`, 1 write-path on Target).

## Iteration write path: pre-state and post-state (re-queried from the LCM)

Pre-state (Target `PhonologicalDataOA.ContextsOS`): **0 contexts**, no
`TEST_` rows. Target holds 1 phoneme set with 2 `IPhBdryMarker`s (`+`, `#`).

Post-state, re-queried from `ContextsOS` after the write (never asserted off
the objects just built):

| Object | `min_count` | `max_count` | `member.context_name` |
|---|---|---|---|
| `TEST_572_US1_iter_unbounded` (Min 1, Max -1) | 1 | `None` | `TEST_572_US1_member` |
| `TEST_572_US1_iter_bounded` (Min 0, Max 3) | 0 | 3 | `TEST_572_US1_member` |

`filter(name_contains="TEST_572_US1_")` matched 3 (member + both iterations).
Restore: all three removed in `finally:`; pool count back to **0** (verified
by a separate read-only open after the run).

## Read-only findings on `morphboundary` (SC-004, C10)

- 7 pooled contexts (6 `PhSimpleContextSeg`, 1 `PhSimpleContextBdry`) plus
  every rule-referenced left/right context: `context_name` and `description`
  contain no `SIL.LCModel` substring anywhere.
- The `PhSimpleContextBdry` (left of `a insertion`) reports
  `is_boundary_context is True`, a non-`None` `boundary_marker`, a non-empty
  `boundary_name` (`+`), and a non-`None` `as_boundary_context()`.
  `boundary_contexts()` over the pool is non-empty.
- Each `PhSequenceContext` reports `is_sequence_context` with 2-3 members.
- C10 control: raw `ContextsOS[0]` (narrowed `IPhContextOrVar`) has no
  `FeatureStructureRA`, while the wrapper's `.segment` resolves -- the read
  goes through `_concrete`.

## Two deviations from tasks.md T003, recorded here (not silently)

1. Every pre-existing context `Name` in `morphboundary` is unset
   (`StringCount == 0`, BestAnalysis `***`), so the honest `context_name` is
   `""` and no positive `filter(name_contains=<pre-existing name>)` match
   exists. The test asserts the negative (`SIL.LCModel` matches nothing) on
   `morphboundary` and the positive match (`TEST_572_US1_` matches 3) on
   Target. Sequence members are likewise unnamed pre-existing data; their
   non-empty-name proof is the `TEST_` member.
2. `cast_to_concrete()` had no entries for `PhSimpleContextBdry`,
   `PhSequenceContext` or `PhIterationContext`, so `_concrete` stayed
   narrowed and every concrete-only member read as absent (measured: bdry
   and sequence contexts never left `IPhPhonContext`). `T005` therefore
   extends `flexicon/code/lcm_casting.py` with those three registrations
   (plus a Supported-Types doc line). No other behavior of that module
   changes. Because a shared file was touched, the Phase 6 full offline
   gate must confirm no regression (T027 owns it).

## Checkpoint (Phase 3 US1)

Full offline gate after the contract-baseline regeneration:
`2577 passed, 1086 deselected` (baseline `2575 passed, 1081 deselected`;
delta `+2` is the two new mock tests, `+5` deselected is the new live file).
`test_no_new_type_dependencies` required the mechanical regeneration of
`tests/contract/snapshots/expected_contract.json` (`+3` unique imports:
`IPhBdryMarker`, `IPhIterationContext`, `IPhSimpleContextBdry`, all
live-verified present).

Every context in a live project describes itself through
`PhonologicalContext` alone, and the iteration reader is proven on
constructed data (SC-004, SC-008 iteration half). US1 files only:
`flexicon/code/System/phonological_context.py`,
`flexicon/code/System/context_collection.py`,
`flexicon/code/lcm_casting.py` (C10 prerequisite, see deviation 2),
`tests/test_context_wrappers.py`,
`tests/operations/test_issue572_context_readers_live.py`, this file.
