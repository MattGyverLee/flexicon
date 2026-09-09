# Cycle 3 -- Verification report (issue #270 Tier 4)

**Verdict: PASS**

## Command and run_mode

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_collection_cast_pattern.py -m requires_live_project -q -rs
```
Result: `4 passed, 68 deselected`. `tests/live_status.json` ->
`"run_mode": "live"`. Confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
-> `live`.

## Test names -> Tiers

- `test_complex_form_component_round_trip` (target_sandbox) -- Tier 1
- `test_possibility_items_expose_subtype_surface` (sena3_sandbox) -- Tier 3
- `test_subitem_recursion_reaches_grandchildren` (sena3_sandbox) -- Tier 3
- `test_chart_cell_tag_getall_is_not_empty_when_tags_exist` (target_sandbox) -- **Tier 4** (the fix under review)

All 4 passed. `live_status.json.by_class` corroborates per-class pass status.

## Proof of execution (the crux of this cycle)

Two independent methods on a scratch in-place edit, both reverted:
1. Transient `print()` before the assertion showed real re-queried HVOs:
   `expected=[10446, 10447] actual=[10446, 10447]`.
2. Inverted the assertion to `len(actual)==999 and actual==[]`; the test
   genuinely FAILED with `assert (2 == 999)`, proving it is not vacuously
   green.
3. (Bonus) Instrumented the cleanup loop; both `marker` and `col`
   confirmed deleted (old bug leaked `col` via a misplaced `return`).

`sha256sum` of the test file matched before the first edit and after the
final revert; `git status --porcelain` shows only the pre-existing
programmer diff, no residue.

## Post-state

Re-queried from the LCM after the write (`row.CellsOS` directly, and
`ConstChartCellTagOperations.GetAll(row)`), not from the values passed
in. Both equal `[10446, 10447]`.

## Correction applied

Appended a dated CORRECTION section to
`evidence/live-270-tier34.md` (cycle 1): the Tier 4 skip was never a
genuine "Sena 3 has no constituent charts" data-shape gap. Cycle 1's own
code used `sena3_sandbox.ConstChart` (singular), but `FLExProject`
defines only `ConstCharts` (plural) with no `__getattr__`, so that line
raised `AttributeError` unconditionally and the `pytest.skip` two lines
later was unreachable. The genuine cause was an accessor typo,
independently confirmed by cycle 2's diagnosis. Tiers 1-3 stand; their
live status should now be cited from cycle 2's/cycle 3's runs, not solely
cycle 1's file.

## Blockers

None. Target was present and unlocked (`restore_target.py --check` ->
present); `target_sandbox`/`sena3_sandbox` used throughout, so nothing
touched the real projects.

## Recommendation

APPROVE. Evidence:
`specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-committed.md`
(new) and the appended correction in
`specs/269-272-casting-and-factory-seam/evidence/live-270-tier34.md`.
