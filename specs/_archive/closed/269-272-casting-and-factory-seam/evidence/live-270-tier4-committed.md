# Live verification -- issue #270 Tier 4 (committed/fixed test, cycle 3)

**Project:** Target | **Fixture:** target_sandbox (tempdir copy of the Target
`.fwbackup`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_collection_cast_pattern.py -m requires_live_project -q -rs
```
**run_mode:** live (`tests/live_status.json` -> `"run_mode": "live"`,
`"run_timestamp": "2026-09-09T16:08:21Z"`)
**Date:** 2026-09-09

## Claim under test

`ConstChartCellTagOperations.GetAll(row)` returns the `ConstChartTag`
objects actually present in `row.CellsOS` (pre-fix `isinstance` filter
over CellsOS matched nothing and always returned `[]`, issue #270 Tier 4).

Cycle 3 additionally verifies that the programmer's two repairs to the
test itself (a `return` misplaced inside a `for` loop in `finally:`, and
an orthogonal `label=` argument that triggered an unrelated write-path
bug in `ConstChartRowOperations.Create`) actually let the Tier 4
assertion execute, rather than being silently skipped as in cycle 2.

## Test names -> Tiers (this run, verbose)

```
tests/operations/test_collection_cast_pattern.py::TestCollectionCastLive::test_complex_form_component_round_trip PASSED
tests/operations/test_collection_cast_pattern.py::TestCollectionCastLive::test_possibility_items_expose_subtype_surface PASSED
tests/operations/test_collection_cast_pattern.py::TestCollectionCastLive::test_subitem_recursion_reaches_grandchildren PASSED
tests/operations/test_collection_cast_pattern.py::TestCollectionCastLive::test_chart_cell_tag_getall_is_not_empty_when_tags_exist PASSED
4 passed, 68 deselected in 8.86s
```

| Test name | Tier | Fixture |
|---|---|---|
| test_complex_form_component_round_trip | Tier 1 (Get/Add composability) | target_sandbox |
| test_possibility_items_expose_subtype_surface | Tier 3 (subtype surface) | sena3_sandbox |
| test_subitem_recursion_reaches_grandchildren | Tier 3 (recursion) | sena3_sandbox |
| test_chart_cell_tag_getall_is_not_empty_when_tags_exist | **Tier 4** (isinstance filter over CellsOS) | target_sandbox |

`tests/live_status.json` `by_class` corroborates: `LexEntryOperations.add`
= pass, `PossibilityListOperations.read` = pass (2 tests),
`ConstChartCellTagOperations.add` = pass.

## Pre-state (read from LCM)

Immediately after row creation, before any cell-tag is added:
`row.CellsOS.Count == 0` (asserted in the test body and held on this run).

## Action

```python
col = markers.Create("TEST_270_col")
marker = markers.Create("TEST_270_tag")
chart = charts.Create("TEST_270_chart")
row = rows.Create(chart)                      # label= omitted (see below)
created_tags.append(cell_tags.Create(row, col, marker))
created_tags.append(cell_tags.Create(row, col, marker))
```

`label=` was dropped from `rows.Create(chart)` because
`ConstChartRowOperations.Create` calls `new_row.Label.set_String(...)`,
but `Label` on `IConstChartRow` is a bare `ITsString` with no
`set_String` method (confirmed live: `AttributeError`). That write-path
bug is orthogonal to the Tier 4 claim under test and is tracked
separately; omitting `label=` routes around it without touching
production code.

## Post-state (re-queried from the LCM after the write)

```python
expected = [c.Hvo for c in row.CellsOS if c.ClassName == "ConstChartTag"]
actual = [t.Hvo for t in cell_tags.GetAll(row)]
```

Observed via a transient `print()` instrumentation (proof-of-execution
method 1, see below) placed on the exact line between `actual = ...` and
the `assert`:

```
TIER4_PROOF expected=[10446, 10447] actual=[10446, 10447]
```

Both lists are populated from re-queries of the live LCM after the
write -- `expected` from `row.CellsOS` directly, `actual` from
`ConstChartCellTagOperations.GetAll(row)` -- not from `created_tags`
(the values passed in). `len(actual) == 2 and actual == expected` held.

## Proof that the test's own assertion actually executed

Two independent methods were used, both on a disposable in-place edit
of the committed test file, each fully reverted afterward (see Cleanup):

**Method 1 -- transient print of expected/actual.** Inserted
`print(f'TIER4_PROOF expected={expected} actual={actual}')` immediately
before the assertion line and re-ran with `-s`. Output above shows real
HVOs (`10446, 10447`) computed live, proving the code reached that line
with genuine data rather than short-circuiting via the old `return`-in-
`finally` bug (which previously swallowed any exception raised earlier
in the `try` block, including the pre-fix `AttributeError` from
`label=`).

**Method 2 -- invert the assertion to confirm the test CAN fail.**
Changed the assertion to `assert len(actual) == 999 and actual == []`
and re-ran. Result: genuine failure --
```
E   AssertionError: GetAll returned [10446, 10447], expected [10446, 10447]. ...
E   assert (2 == 999)
E    +  where 2 = len([10446, 10447])
```
This confirms the test is not vacuously green: it fails when the real
Tier 4 mechanism's output does not match a deliberately wrong
expectation, and passes only because `GetAll` genuinely returns the
correct two HVOs.

**Method 3 (bonus) -- cleanup loop proof.** Instrumented the `finally`
block's `for item in (marker, col): ... markers.Delete(item)` with a
print after each successful delete. Output:
```
TIER4_CLEANUP_PROOF deleted hvo=-2
TIER4_CLEANUP_PROOF deleted hvo=-2
```
Both loop iterations executed and both `Delete()` calls succeeded (no
`FAILED` line), confirming the old defect -- a `return` inside the loop
that stopped after deleting only `marker` and leaked `col` -- is fixed.
(`-2` is the LCM's post-delete sentinel Hvo value on the now-invalid
proxy for both objects; the point under test is that both branches ran
without exception, which they did.)

All three edits were made directly to
`tests/operations/test_collection_cast_pattern.py`, run once each, then
reverted. `sha256sum` of the file was identical before the first edit
and after the final revert
(`d9d4ac0923cfd58b9bf2c2836e7677dcdfc111835b36121ef83baa4e2df1f68e`), and
`git diff --stat` after all edits reverted matches the original
programmer diff exactly (63 insertions / 27 deletions, same as before
any experiment). `git status --porcelain` confirms no stray files.

## Cleanup

Both marker vocabulary items (`TEST_270_col`, `TEST_270_tag`) and the
chart (`TEST_270_chart`, which cascades to delete its row and cell-parts)
were deleted inside the test's own `finally:` block, confirmed via Method
3 above to execute for both loop iterations. `target_sandbox` is itself a
tempdir copy of the Target `.fwbackup`, discarded by fixture teardown
regardless, so nothing could leak to the real Target
(`C:\ProgramData\SIL\FieldWorks\Projects\Target`) even had cleanup
failed.

## Result

**[PASS]** -- `run_mode: live`; all 4 `TestCollectionCastLive` tests
passed; the Tier 4 test's own assertion demonstrably executed (proven by
two independent methods) and re-queried the LCM post-write; both
temporary marker objects are now confirmed deleted by the fixed cleanup
loop.
