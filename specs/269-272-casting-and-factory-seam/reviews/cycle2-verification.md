# Verification Report -- issue #270 Tier 4 (cycle 2, target_sandbox retarget)

**Verdict:** FAIL: unverified
**Live run:** yes | **run_mode:** live
**Evidence:** specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-target.md
**Project:** Target (target_sandbox)

## Command and run_mode

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_collection_cast_pattern.py -m requires_live_project -q -rs
```
Result: 4 passed, 68 deselected. tests/live_status.json: run_mode = live,
run_timestamp = 2026-09-09T15:57:21Z.

## Claim vs observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| ConstChartCellTagOperations.GetAll(row) returns the tags in row.CellsOS (Tier 4 fix) | Never exercised by the shipped test; verified separately via a disposable diagnostic (HVOs [10446, 10447] matched on both sides after re-query) | mechanism PASS, shipped test FAIL: unverified |
| Accessor-typo fix (ConstChart -> ConstCharts) makes the test executable | True, collection/import no longer AttributeErrors on that line | PASS |
| Fixed test now reaches its Tier 4 assertion on target_sandbox | FALSE. rows.Create(chart, label="TEST_270_row") raises AttributeError ("ITsString has no attribute set_String", ConstChartRowOperations.py:132) before the assertion is ever reached | FAIL |
| pytest 4 passed proves the fix | FALSE. The AttributeError above is silently swallowed by a return statement misplaced inside the test own finally: block (line 1053, indented inside the for-loop over (marker, col)), which also skips deleting col | FAIL |

## Two defects found (full detail in evidence file)

1. Defect A (pre-existing, unrelated to #270): ConstChartRowOperations.Create
   calls new_row.Label.set_String(...) but Label on IConstChartRow is a
   bare ITsString with no set_String method -- crashes whenever label= is
   passed with a truthy value.
2. Defect B (introduced by this cycle's fix): a return statement inside
   the test finally block is indented inside the for-loop over
   (marker, col), so it fires unconditionally after the first iteration.
   A return inside finally suppresses any exception from the try block
   (confirmed by isolated repro), which is why pytest reports the test as
   passed despite Defect A crashing it, and also leaks col (never
   deleted) and leaves a dead pytest.skip line unreachable.

The Tier 4 GetAll mechanism itself was independently verified live and is
correct (see evidence file), but the shipped test cannot be trusted as
its verification, since it never runs its own assertion.

## Corrected diagnosis of the cycle-1 skip

Cycle 1 (reviews/cycle1-verification.md and
evidence/live-270-tier34.md) attributes the Tier 4 skip to "Sena 3 has no
constituent charts" (a genuine data-shape skip). This is wrong. The
pre-fix code was sena3_sandbox.ConstChart.GetAll() (singular, no
ConstChart property exists on FLExProject, no __getattr__ override
defined) -- this raises AttributeError unconditionally, before the
pytest.skip two lines later can ever run, regardless of Sena 3 content.
Cycle 1 causal claim could not have been produced by the code as it
existed. The correct diagnosis is cycle 2 programmer own diagnosis: an
accessor typo, not missing data.

## Mock suite

Not run this cycle; out of scope for this task (live-only verification
requested).

## Blockers

None for reaching a live run. However the shipped test is not valid
evidence of the Tier 4 claim due to Defects A and B above; these need a
follow-up fix (drop label= from the Create call, or fix
ConstChartRowOperations.Create's Label handling; and dedent/remove the
return from inside the finally for-loop so both markers are cleaned up
and real failures propagate).

## Recommendation

FIX ISSUES -- do not merge/report Tier 4 as verified on the strength of
this test's green result. Fix Defect B (return-in-finally) at minimum so
the test can genuinely fail, and fix or route around Defect A
(ConstChartRowOperations.Create label= bug) so the test's own assertion
actually executes. The underlying GetAll fix is confirmed correct by an
independent live diagnostic, but that diagnostic is not part of the
committed test suite and does not substitute for a working committed
test.
