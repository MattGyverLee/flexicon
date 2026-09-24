# Issue #357 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** `fix/357-wordgroup-ra` from `origin/main`

## Triage

| Priority | Open without PR |
|----------|-----------------|
| P0 | none |
| P1 | none |
| P2 | none (each open P2 already has an in-flight PR) |
| **Selected** | **P3 #357** -- verify/fix `WordGroupRA` phantom on clause markers |

## RULING (binding)

1. **`WordGroupRA` is not on `IConstChartClauseMarker`.** Contract baseline
   (`liblcm_baseline.json`) lists `ColumnRA` and `DependentClausesRS` only;
   `WordGroupRA` is on `IConstChartMovedTextMarker` (R5 / #290 model).

2. **`Create` is correct on main:** attach via `row.CellsOS`, set `ColumnRA`
   from the supplied word group; do **not** set `WordGroupRA` (#324 ruling).

3. **`GetWordGroup` must not read `WordGroupRA` on clause markers.** Navigate
   the owning row's `CellsOS`: return the `ConstChartWordGroup` whose
   `ColumnRA` matches the marker's `ColumnRA` (HVO match when available).
   Return `None` when `ColumnRA` is unset or no cell matches.

4. **Live verification:** When FieldWorks is available, create a marker with
   `Create(row, wg)` and assert `GetWordGroup(marker)` round-trips to the
   same word group HVO as `wg`.

## Out of scope

- Moved-text marker navigation (unchanged; uses `WordGroupRA`).
- Factory `Create(row, index, column, dependents)` overload.
