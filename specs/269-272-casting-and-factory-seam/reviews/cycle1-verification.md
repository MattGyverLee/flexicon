# Verification Report -- issue #270 Tiers 3/4 (cycle 1)

**Verdict:** [PASS] for 2 of 3 assertions; [FAIL: unverified] for the third
**Live run:** yes | **run_mode:** live (both runs)
**Evidence:** specs/269-272-casting-and-factory-seam/evidence/live-270-tier34.md
**Project:** Sena 3 (sena3_sandbox -- tempdir copy, real Sena 3 never opened)

## Claim vs. observed (issue #270, Tiers 3/4)

| Claim | Observed live | Status |
|-------|---------------|--------|
| Tier 3: `GetItems` elements are cast to `IPartOfSpeech`, expose `DefaultInflectionClassRA` | 11/11 Parts-of-Speech items: `ClassName == "PartOfSpeech"`, `hasattr(item, "DefaultInflectionClassRA") == True` | [PASS] |
| Tier 3 (recursion): `GetSubitems(recursive=True)` reaches grandchildren | Semantic domain hvo=58915: direct=7, recursive=105 (105 > 7); direct Hvo set ⊆ deep Hvo set | [PASS] |
| Tier 4: `ConstChartCellTagOperations.GetAll(row)` returns the `ConstChartTag`s actually in `row.CellsOS` | **SKIPPED** -- `project.ConstChart.GetAll()` returns 0 charts in this Sena 3 backup. No row, no cell, nothing to assert against. | [FAIL: unverified] |

pytest's own summary for this class:
`3 passed, 1 skipped, 68 deselected` (`test_collection_cast_pattern.py`,
`-m requires_live_project -rs`). The single skip is exactly the Tier 4
test above -- per CLAUDE.md's rule, a skip is not a pass and is reported
as `FAIL: unverified`, not folded into "no failures."

## Data-shape finding for the Tier 4 skip (for a follow-up cycle)

Probed the same `sena3_sandbox` in the same session (disposable pytest
file, deleted after one run, no artifacts left):

- `project.ConstChart.GetAll()` -> **0 charts** in
  `Sena 3 2018-09-11 1145.fwbackup`. There is no Discourse Chart of any
  kind in this snapshot, so there are no rows and no `ConstChartTag`
  cells to exercise. This is a genuine absence of preconditions in the
  fixture data, not a fixture-availability problem or a code defect --
  the rest of the file's tests (and the 74 tests in the #278 run below)
  executed normally against the same sandbox.
- Recommendation for retargeting: build the chart/row/tag precondition
  on a **Target sandbox** (create the chart, row, and a `ConstChartTag`
  cell directly, mirroring how Tier 1's
  `test_complex_form_component_round_trip` creates its own data rather
  than relying on Sena 3 already containing it), or source a different
  Sena 3 snapshot known to contain a Discourse Chart. Either is a new,
  separate task; not attempted here per instructions (verification only,
  no production/test changes).

## #278 fixture gate (separate, per instructions)

Ran the 11 previously-blocked sena3-dependent files:

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_allomorphs_live.py \
  tests/operations/test_etymologies_live.py tests/operations/test_examples_live.py \
  tests/operations/test_feature_struc_resolver.py tests/operations/test_issue254_live_cycle2.py \
  tests/operations/test_issue254_morphra_probe.py tests/operations/test_lexentry_resolve_object_live.py \
  tests/operations/test_locations_live.py tests/operations/test_persons_live.py \
  tests/operations/test_pronunciations_live.py tests/operations/test_variants_live.py \
  -m requires_live_project -q -rs
```

Result: **74 passed, 3 skipped, 0 errors** (was 23 ERRORs, all
"sena3_sandbox unavailable", in the 2026-09-08 evidence run before the
fixture file existed). `run_mode: live`.

The 3 skips are unrelated to fixture availability and each carries its
own documented rationale in the test itself:
- `test_locations_live.py:312` -- Sena 3 has zero pre-existing locations;
  Phase B already covers Delete on self-created objects.
- `test_persons_live.py:174` -- `lp.PeopleOC` is an unordered collection;
  reorder is inapplicable.
- `test_pronunciations_live.py:378` -- sandbox has no entries with
  `PronunciationsOS` items.

None of these is a new defect and none is a #270/#278 blocker. Not filing
as a new issue -- they are pre-existing, self-documented data-shape
skips, not failures.

**#278 verdict: CLEAR.** The missing-fixture blocker is resolved; zero
"sandbox unavailable" errors remain.

## Unrelated failures found

None. Both runs: 0 failures, 0 errors, only the accounted-for skips above.

## Mock suite (regression, supplementary)

Not run this cycle -- out of scope for this verification-only task (no
production code was touched; scope was strictly the two live pytest
invocations specified).

## Blockers

None requiring escalation. Tier 4's skip is a data-shape gap in the
current Sena 3 fixture snapshot, not a blocker to close this cycle's
task -- it is reported above as follow-up work.

## Recommendation

APPROVE the #278 fixture-resolution claim (CLEAR, 0 errors).
For #270: Tiers 1-3 are now live-verified (Tier 1 was already verified in
the prior evidence file; Tier 3 and its recursion sub-case are newly
verified live in this cycle). **Tier 4 remains FAIL: unverified** and
should stay open, tracked as a follow-up task to retarget the test against
data that actually contains a constituent chart (Target-sandbox-created
or an alternate Sena 3 snapshot).

## Bottom line

**#270 Tiers 3/4: PARTIAL -- Tier 3 (including recursion) VERIFIED LIVE;
Tier 4 (ConstChartCellTagOperations.GetAll) is FAIL: unverified (skipped
for lack of chart data in the current Sena 3 fixture, not a code defect).**
