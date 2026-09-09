# Cycle 3 - Programmer report

Fixed three defects in
`test_chart_cell_tag_getall_is_not_empty_when_tags_exist`
(`tests/operations/test_collection_cast_pattern.py`).

Diff:
1. Line ~1020: `rows.Create(chart, label="TEST_270_row")` -> `rows.Create(chart)`.
   Added a comment explaining `label=` is omitted because
   `ConstChartRowOperations.Create` calls `new_row.Label.set_String(...)`
   but `Label` on `IConstChartRow` is a bare `ITsString` with no
   `set_String` (confirmed live: AttributeError), and this write-path bug
   is orthogonal to the Tier 4 claim under test and tracked separately.
   Production code untouched.
2. Removed the bare `return` that sat inside the
   `for item in (marker, col):` loop inside `finally:` (previously line
   1053). It suppressed any exception from the `try` body and stopped the
   loop after deleting only `marker`, leaking `col`. Both markers are now
   always deleted.
3. Removed the unreachable trailing
   `pytest.skip("No chart row with a ConstChartTag found in Sena 3")`
   (previously line 1054), dead code left over from the pre-fix Sena 3
   version.

Final method now spans lines 993-1051 (was 993-1054); no other test
touched.

Verification: `python -m pytest tests/operations/test_collection_cast_pattern.py --collect-only -q`
-> "72 tests collected in 1.35s", no errors. Live suite not run, per
instructions - left to a verifier.
