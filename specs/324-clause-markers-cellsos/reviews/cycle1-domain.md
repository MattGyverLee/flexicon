# Issue #324 -- /lex-lead domain ruling (cycle 1)

**Issue:** P1 -- `ConstChartClauseMarkerOperations` reads/writes
`IConstChartRow.ClauseMarkersOS`, which does not exist; markers are
cell-parts in `CellsOS`.

**RULING:** REWRITE the four call sites to the established R5 / #270
Discourse model already used by `ConstChartWordGroupOperations`,
`ConstChartCellTagOperations`, and `ConstChartMovedTextOperations`:

1. **Create** -- `factory.Create()` then `row.CellsOS.Add(marker)` before
   property setters; set `ColumnRA` from `word_group.ColumnRA` when present.
   Do **not** use `ClauseMarkersOS`. Do **not** set `WordGroupRA` on the
   marker (`IConstChartClauseMarker` has no such member; tracked separately
   in #232).

2. **Find / GetAll** -- filter `row.CellsOS` with
   `ClassName == "ConstChartClauseMarker"`, then `_GetTypedElements`
   (issue #270 cast pattern).

3. **_GetSequence** -- return `parent.CellsOS` (reordering operates on the
   row cell sequence; same as word groups).

**Out of scope:** `GetWordGroup` / `WordGroupRA` phantom reads (#232);
factory `Create(row, index, column, dependents)` overload exploration;
broader Discourse chart API changes.

**Live verification:** Required -- assert marker HVO appears in
`row.CellsOS` after Create and is returned by `GetAll` / `Find`.
