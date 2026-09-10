# Live verification -- issue #290 pre-fix reflection pass

**Project:** Target | **Fixture:** target_sandbox (tempdir copy of the
Target .fwbackup, undoable=False)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue290_const_chart_reflection.py -m requires_live_project -q -rs
```
(executed via the equivalent `export FLEXLIBS_REQUIRE_LIVE=1 && python -m
pytest ...` under Git Bash; behaviour is identical, the env var is read
by tests/conftest.py regardless of shell)

**run_mode:** live (tests/live_status.json: "run_mode": "live",
"run_timestamp": "2026-09-10T18:15:05Z")
**Date:** 2026-09-10
**Test file:** tests/operations/test_issue290_const_chart_reflection.py
(new, 3 tests, all passed)
**Raw JSON evidence:** specs/299-300-290-reorder-and-tsstring/evidence/live-290-reflection-raw.json

## Scope

This cycle gathers the live reflection evidence issue #290 says must
exist before any fix is written. No production code was modified. All
five numbered questions in the issue are resolved below from live
type()/GetType()/dir()/hasattr() output and live tracebacks, never from
analogy.

## Claim under test

Five UNDETERMINED items from issue #290:
1. IConstChartRow.Label CLR type (bare ITsString claim)
2. IConstChartRow.Notes CLR type (UNDETERMINED, needs isolating hit)
3. GetLabel/GetNotes .get_String(ws) behaviour
4. Reachability of the hasattr(cell, "Label") branch at
   DiscourseOperations.py:888/950 for the four real cell-part types
5. Whether the sibling Comment branch at DiscourseOperations.py:892
   targets a genuine IMultiString

## Q1 -- IConstChartRow.Label CLR type

Pre-state: fresh TEST_290_chart_labelnotes chart, row created via
rows.Create(chart) with no label/notes args (so the already-known
line-132 crash cannot fire and this row is safe for pure reflection).

Action: type(plain_row.Label), plain_row.Label.GetType().FullName,
hasattr(plain_row.Label, "set_String"),
hasattr(plain_row.Label, "get_String").

Observed (live, re-queried from the LCM object just created):
```
q1_label_py_type:            ITsString
q1_label_clr_type:           SIL.LCModel.Core.Text.TsString
q1_label_has_set_String:     false
q1_label_has_get_String:     false
```
dir(plain_row.Label) (29 members) contains no get_String/set_String --
only Text, get_Text, GetChars, GetBldr, FetchRunInfo*, Length, RunCount,
etc. -- the bare-ITsString surface, not an IMultiString.

Result: CONFIRMED. Issue claim is correct: IConstChartRow.Label is a
bare ITsString (SIL.LCModel.Core.Text.TsString), not an IMultiString.
Matches Category 8 (Source, BaselineText).

## Q2 -- IConstChartRow.Notes, isolating live hit

Action: rows.Create(chart, label=None, notes="TEST_290_notes") on the
same chart -- label=None is falsy, so the "if label:" guard at line 130
is skipped and execution reaches line 137 (new_row.Notes.set_String)
without ever touching line 132's already-confirmed Label bug. This is
the isolating hit the issue asked for.

Observed (live traceback, re-queried, not asserted from the call args):
```
AttributeError: ITsString object has no attribute set_String.
Did you mean: ToString.
  flexicon/code/Discourse/ConstChartRowOperations.py:137, in Create
    new_row.Notes.set_String(wsHandle, mkstr)
```
Also captured directly on the same plain_row used for Q1:
```
notes_py_type:            ITsString
notes_clr_type:           SIL.LCModel.Core.Text.TsString
notes_has_set_String:     false
notes_has_get_String:     false
```
dir(plain_row.Notes) is byte-for-byte the same 29-member bare-ITsString
surface as Label.

Result: CONFIRMED BROKEN, independently of the Label crash.
IConstChartRow.Notes is a bare ITsString, same defect class as Label.
The previously UNDETERMINED rows for lines 137 and 414 are now
resolved: both call set_String on a field with no such method.

## Q3 -- GetLabel (line 299) / GetNotes (line 375), live

Action: rows.GetLabel(plain_row) and rows.GetNotes(plain_row) on the
same row (Label/Notes present but unset).

Observed (live tracebacks):
```
GetLabel -> AttributeError: ITsString object has no attribute get_String.
Did you mean: ToString.
  ConstChartRowOperations.py:299, in GetLabel
    return ITsString(row.Label.get_String(wsHandle)).Text or ""

GetNotes -> AttributeError: ITsString object has no attribute get_String.
Did you mean: ToString.
  ConstChartRowOperations.py:375, in GetNotes
    return ITsString(row.Notes.get_String(wsHandle)).Text or ""
```

Result: CONFIRMED BROKEN. The "Bonus finding" in the issue (get_String
on a bare ITsString raises) is confirmed live for both getters, not
just predicted by analogy to BaselineText.

## Q4 -- reachability of DiscourseOperations.py:888 (and the mirrored
read at :950) for real cell-parts

Built a real row with a real word group (referencing a live ISegment
from a throwaway TEST_290_text) and a real ConstChartTag
(cell_tags.Create(row, col, marker)), then reflected on live instances
of all four concrete cell-part types named in the issue:

| Type (ClassName, live) | Obtained via | hasattr Label | hasattr Comment |
|---|---|---|---|
| ConstChartWordGroup | word_groups.Create(row, seg, seg) | false | false |
| ConstChartTag | cell_tags.Create(row, col, marker) | false | false |
| ConstChartClauseMarker | clause_markers.Create(row, word_group) | false | false |
| ConstChartMovedTextMarker | raw factory + MovedTextMarkerOA (see note) | false | false |

Note on ConstChartMovedTextMarker: the documented
ConstChartMovedTextOperations.Create(word_group, preposed=True) itself
raised live (System.NullReferenceException in
ConstChartMovedTextMarker.set_Preposed, reproduced a second time in
isolation by setting .Preposed = True directly on a raw-factory
instance) -- an unrelated pre-existing defect, out of #290 scope, not
touched or fixed here. To still get a live instance for the Q4
reflection, the diagnostic bypassed only the Preposed setter (raw
IConstChartMovedTextMarkerFactory.Create() plus
word_group.MovedTextMarkerOA = new_marker, the same two lines
ConstChartMovedTextOperations.py:124-128 already perform). Full live
dir() (86 members) confirms the real property surface: ColumnRA,
WordGroupRA, Preposed, Guid, Hvo, ClassName, etc. -- no Label, no
Comment.

Additional live reachability check -- exactly the caller path
(DiscourseOperations.GetCells(row) -> SetCellContent/GetCellContent),
not a hand-built object:
```
live_getcells_row_cellsos_count: 2   (word group + tag; the clause
                                      marker was NOT added to
                                      row.CellsOS -- see below)
GetCells(row) -> [ConstChartWordGroup(hvo=10452), ConstChartTag(hvo=10453)]

SetCellContent(word_group, "TEST_290_content")
  -> raised FP_ParameterError: Cell does not support editable content
     (no Label or Comment property)
GetCellContent(word_group) -> success: ''

SetCellContent(tag, "TEST_290_content")
  -> raised FP_ParameterError: Cell does not support editable content
     (no Label or Comment property)
GetCellContent(tag) -> success: ''
```
Both real cells fell straight through the hasattr(cell, "Label") and
hasattr(cell, "Comment") branches to the final else: raise
FP_ParameterError. Neither branch fired.

Bonus finding (separate defect, out of #290 scope, not fixed here):
clausemarker_in_row_cellsos: false -- ConstChartClauseMarkerOperations
.Create checks hasattr(row, "ClauseMarkersOS"), which is false on a
real IConstChartRow; the marker is created and returned but never
attached to row.CellsOS (or anywhere else reachable), so it is also
never seen by GetCells/SetCellContent/GetCellContent in practice.
ConstChartMovedTextMarker is likewise never a CellsOS member -- it is
owned atomically via word_group.MovedTextMarkerOA, not the row cell-part
sequence.

Result: DEAD BRANCH, confirmed live. None of the four concrete
cell-part types exposes a Label field. The hasattr(cell, "Label")
branch at DiscourseOperations.py:888 (and the mirrored read at :950)
cannot fire for any real cell obtained via GetCells(row) in this
project -- confirmed both by direct reflection on live instances of all
four types and by actually driving SetCellContent/GetCellContent
through the real two reachable cell types and observing them fall
through to the FP_ParameterError branch.

## Q5 -- DiscourseOperations.py:892 Comment branch, type

Action: hasattr(obj, "Comment") on live instances of all four concrete
types (same objects as Q4).

Observed:
```
wordgroup_has_comment:     false
tag_has_comment:           false
clausemarker_has_comment:  false
movedtext_direct_has_comment: false
```
None of the four concrete cell-part types has a Comment field at all in
this live schema (liblcm baseline for this run). The
"elif hasattr(cell, 'Comment')" branch at DiscourseOperations.py:892 is
therefore equally unreachable for any of the four real cell-part types
-- it never gets a chance to demonstrate whether it is a genuine
IMultiString, because no live cell-part instance observed here ever
satisfies the hasattr check that guards it.

Result: recorded, not changed, per the issue explicit instruction. No
live cell-part instance in this project exposes Comment, so this run
cannot determine live whether Comment is a genuine IMultiString on some
other reachable type; it only confirms the Comment branch is equally
dead for the four types Q4 already covers. The issue belief that
Comment is "believed genuinely correct" for some other type (e.g. an
annotation Comment) is neither confirmed nor refuted by this run and
must not be touched by any #290 fix, consistent with the issue explicit
warning.

## Cleanup

All charts, markers (TEST_290_col, TEST_290_marker), and throwaway texts
(TEST_290_text, TEST_290_text_mtm) created during this run were deleted
via their Operations .Delete() calls in each test finally: block.
target_sandbox is additionally a tempdir copy of the Target .fwbackup,
discarded entirely by fixture teardown regardless of cleanup success;
the real Target project (tests/fixtures/Target 2026-07-06 0218.fwbackup)
was never opened by this verification -- target_sandbox, not
target_project, was used throughout. git status --porcelain after the
run shows only the new test file and this evidence pair as additions;
no production file was touched.

## Result

| Q | Verdict |
|---|---|
| Q1 -- Label bare ITsString | CONFIRMED |
| Q2 -- Notes bare ITsString (isolating hit) | CONFIRMED BROKEN |
| Q3 -- GetLabel/GetNotes raise on get_String | CONFIRMED BROKEN |
| Q4 -- hasattr(cell,"Label") branch reachability | DEAD BRANCH (confirmed live for all 4 types plus real GetCells path) |
| Q5 -- Comment branch type | Equally dead for all 4 types observed here; genuine-IMultiString claim for any other type neither confirmed nor refuted; left untouched per issue instruction |

[PASS] -- all five questions resolved from live evidence; nothing
UNDETERMINED remains for #290 pre-fix checklist. No fix was written or
attempted in this cycle.
