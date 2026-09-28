# Cycle 3 -- Domain adjudication: `set_String` on bare `ITsString` (Category 8)

Read-only analysis. No files edited, no issue filed, no LCM write performed.

## PROVENANCE AND A REAL LIMITATION -- read this first

lex-domain is provisioned with Read/Grep/Glob/WebFetch only. It therefore had
**no Bash tool and could not run the live `type()`/`dir()` reflection the task
asked for**, and no Write tool to persist this file (persisted by the main
session instead).

It did not fabricate reflection results. Instead it used the live traceback
already recorded in `evidence/live-270-tier4-target.md` for site 132, plus
static/documentary analysis for the other four sites, and marked everything it
could not establish as **UNDETERMINED**. Treat the UNDETERMINED rows as
genuinely open: they need a live reflection pass before any fix is written.

## Per-site adjudication

| Site | Call | Live evidence | Real LCM type | `set_String` exists? | Correct form | Verdict |
|---|---|---|---|---|---|---|
| `ConstChartRowOperations.py:132` (Create, `label=`) | `new_row.Label.set_String(ws, mkstr)` | **Yes** -- `evidence/live-270-tier4-target.md`: `AttributeError: ITsString object has no attribute set_String. Did you mean: ToString.` | `IConstChartRow.Label` = bare `ITsString` | No | `new_row.Label = self._MakeTsString(label, ws)` | **BROKEN (confirmed live)** |
| `ConstChartRowOperations.py:137` (Create, `notes=`) | `new_row.Notes.set_String(ws, mkstr)` | No -- the live run crashed at 132 (label set first), so 137 was never reached | Unconfirmed; same interface, adjacent line, identical pattern | Unknown | If bare `ITsString`: `new_row.Notes = self._MakeTsString(notes, ws)` | **UNDETERMINED, presumed BROKEN by analogy** -- needs an isolating live hit (`notes=` with no `label=`) |
| `ConstChartRowOperations.py:339` (`SetLabel`) | `row.Label.set_String(ws, mkstr)` | Same statement shape on the same field as confirmed-broken 132 | Bare `ITsString` (same field) | No | `row.Label = self._MakeTsString(text, ws)` | **BROKEN (same root cause; same field/type, not independently executed)** |
| `ConstChartRowOperations.py:414` (`SetNotes`) | `row.Notes.set_String(ws, mkstr)` | None; same status as 137 | Unconfirmed | Unknown | If bare `ITsString`: `row.Notes = self._MakeTsString(text, ws)` | **UNDETERMINED, presumed BROKEN by analogy** |
| `DiscourseOperations.py:888` (`SetCellContent`, `hasattr(cell,"Label")` branch) | `cell.Label.set_String(ws, content_str)` | None | Not identifiable statically -- see reachability note | Unknown | n/a until reachability settled | **UNDETERMINED / possibly dead branch** |

## Reachability of `DiscourseOperations.py:888`

`SetCellContent`'s `cell` is documented as an element of `GetCells(row)` -- a
`row.CellsOS` element, hence one of the four concrete cell-part types
(`ConstChartWordGroup`, `ConstChartTag`, `ConstChartClauseMarker`,
`ConstChartMovedTextMarker`; see the `cast_to_concrete` comment at
`DiscourseOperations.py:820-826`). None of the four sibling Operations classes
for those types ever references a `Label` field -- they use `TagRA`,
`WordGroupRA`, `DependentClausesRS`. Only `Comment` is exercised for real
cell-parts elsewhere.

So the `hasattr(cell, "Label")` branch may be **unreachable for any real
cell-part today**, firing only if a caller mistakenly passes an
`IConstChartRow` (which does have `Label`) -- in which case it hits the same
confirmed bug. The mirrored read branch at `GetCellContent` line 950 carries
the same question. Settling this needs live `dir()` on instances of the four
concrete types, not on a row.

## Bonus finding (read side, same field)

`ConstChartRowOperations.py:299` (`GetLabel`) and `:375` (`GetNotes`) call
`row.Label.get_String(ws)` / `row.Notes.get_String(ws)`. Category 8's
`BaselineText` entry in `docs/API_ISSUES_CATEGORIZED.md` states that calling
`.get_String(ws)` on a bare `ITsString` raises `AttributeError` at runtime.
Since `Label` is confirmed bare `ITsString`, the getter is equally broken --
untested only because no live call has reached it. Bundle `GetLabel`/`GetNotes`
into the same fix.

## Draft issue body (NOT filed -- awaiting user approval)

**Title**: `ConstChartRowOperations.Create/SetLabel call set_String on IConstChartRow.Label, a bare ITsString (AttributeError); SetNotes/GetLabel/GetNotes suspect by the same pattern`

**Summary**: A live run against `target_sandbox`, during verification work
related to the bug reported in #270, confirmed that
`ConstChartRowOperations.Create(chart, label=...)` crashes because
`IConstChartRow.Label` is a bare `ITsString`, not an `IMultiString`, and so has
no `set_String`. This is the same same-name/wrong-type trap already catalogued
in `docs/API_ISSUES_CATEGORIZED.md` "Category 8" (`Source`, `BaselineText`).
The identical write pattern appears at `SetLabel` (339), `Create`'s `notes=`
path (137) and `SetNotes` (414); the identical read pattern at `GetLabel` (299)
and `GetNotes` (375). A structurally similar `hasattr(cell, "Label")` branch in
`DiscourseOperations.SetCellContent`/`GetCellContent` (888/950) has unclear
reachability and needs its own live check. **The sibling `Comment` branch at
line 892 is believed correct and must not be touched** -- an annotation's
`Comment` genuinely is a multistring, so a blanket edit would break a working
branch.

**Confirmed live traceback** (`evidence/live-270-tier4-target.md`):
```
AttributeError: ITsString object has no attribute set_String. Did you
mean: ToString.
  flexicon/code/Discourse/ConstChartRowOperations.py:132
```

**Proposed fix**: route the six `Label`/`Notes` accesses on `IConstChartRow`
through the existing `BaseOperations` house idiom for bare-`ITsString` fields
(`_MakeTsString` / `_ReadTsString`, used today for `ILexSense.Source`) rather
than `TsStringUtils.MakeString` + `.set_String`/`.get_String`. Leave
`DiscourseOperations.py:892` alone.

**Write-path caveat**: per CLAUDE.md this is write-path, so any fix needs its
own live verification under `FLEXLIBS_REQUIRE_LIVE=1` against `target_sandbox`,
with pre/post state re-queried from the LCM, written to its own
`evidence/live-<task>.md`. The `Notes` field and the `DiscourseOperations.py:888`
branch need an *independent* live hit -- the existing run never reached them.

**Category 8 update**: yes, a new row for `IConstChartRow.Label` (confirmed
bare `ITsString`) alongside `Source` and `BaselineText`, extended to `Notes`
once independently confirmed.

## Scope

Out of scope for #270 -- this is not a casting defect. Follow-ups #276, #277
and #279 remain open and are untouched by this finding.
