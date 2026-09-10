# Programmer Report -- issue #290 fix (cycle 2)

**Scope:** Fix the six confirmed-broken sites in
`flexicon/code/Discourse/ConstChartRowOperations.py` that treated
`IConstChartRow.Label`/`.Notes` as `IMultiString` when live reflection
(cycle 1) confirmed both are bare `ITsString` fields (Category 8:
same-name field, different LCM type). No other files were touched;
the pre-existing uncommitted #299/#300 work in `BaseOperations.py`,
`DataNotebookOperations.py`, `ParagraphOperations.py`,
`SegmentOperations.py`, `TextOperations.py`,
`WfiMorphBundleOperations.py` is untouched (`git status` confirms).

## Fix

All six sites now route through the house `BaseOperations` idiom,
matching the existing `ILexSense.Source`/`.ScientificName`/
`.ImportResidue` pattern:

- `Create()` (was :130-137): `new_row.Label = self._MakeTsString(label, wsHandle)`
  / `new_row.Notes = self._MakeTsString(notes, wsHandle)`, replacing
  `new_row.Label.set_String(wsHandle, mkstr)` / the Notes equivalent.
- `GetLabel()` (was :299): `return self._ReadTsString(row.Label)`,
  replacing `ITsString(row.Label.get_String(wsHandle)).Text or ""`.
- `SetLabel()` (was :339): `row.Label = self._MakeTsString(text, wsHandle)`,
  replacing `row.Label.set_String(wsHandle, mkstr)`.
- `GetNotes()` (was :375): `return self._ReadTsString(row.Notes)`,
  replacing the `.get_String` equivalent.
- `SetNotes()` (was :414): `row.Notes = self._MakeTsString(text, wsHandle)`,
  replacing `row.Notes.set_String(wsHandle, mkstr)`.

The now-unused `from SIL.LCModel.Core.KernelInterfaces import ITsString`
and `from SIL.LCModel.Core.Text import TsStringUtils` imports were
removed (no remaining call sites in the file).

Out-of-scope items left untouched exactly as instructed:
`DiscourseOperations.py:888/892/950` (confirmed dead branches), the
`ConstChartClauseMarker`/`ConstChartMovedText` bonus bugs (separate
follow-up), and `tests/operations/test_issue290_const_chart_reflection.py`
(re-collected, unchanged, still 3 tests).

## API note flagged (per instructions -- not resolved this cycle)

`GetLabel`/`SetLabel`/`GetNotes`/`SetNotes` keep their public
`ws=None` signature for backward compatibility, but `ws` is now
semantically odd: `Label`/`Notes` are single-valued bare `ITsString`
fields, so there is no per-WS slot to select. Concretely:

- On the **getters**, `ws` is now fully inert -- it is accepted but
  never used, since `_ReadTsString` reads the one stored value
  unconditionally. Docstrings updated to say so explicitly, with an
  "API note (issue #290)" callout asking the domain expert whether the
  parameter should be removed or repurposed.
- On the **setters**, `ws` still has an effect: it tags the WS
  metadata on the single stored `TsString` run (same nuance already
  documented on `LexSenseOperations.SetSource`/`SetScientificName`),
  but it does **not** pick a per-WS slot the way a true multistring
  setter's `ws` would. Docstrings updated to make this distinction
  explicit rather than claiming "uses default analysis writing system"
  as if multiple WS-tagged values could coexist.
- `Create()`'s docstring "Notes" section was similarly corrected to
  stop claiming Label/Notes "use default analysis writing system" in
  the multistring sense.

This is flagged, not resolved -- no signature change was made.

## Tests added

New file `tests/operations/test_290_const_chart_row_tsstring.py`, 13
mock-only tests (no `requires_live_project` marker, no project
opened), covering:

- `TestBareTsStringFixtureShape` -- pins the mock's own shape (no
  `get_String`/`set_String`) and direct falsifiers: calling the OLD
  `.get_String`/`.set_String` pattern on the mock raises
  `AttributeError`, exactly as the live evidence shows.
- `TestGetLabelGetNotesRouteThroughReadTsString` -- `GetLabel`/
  `GetNotes` read a real bare `ITsString`'s text correctly, including
  the empty/unset case (`""`, not `None`).
- `TestSetLabelSetNotesRouteThroughMakeTsString` -- `SetLabel`/
  `SetNotes` round-trip through the getters and leave the field a
  genuine bare `ITsString` (still no `get_String`/`set_String`);
  includes a clear-to-empty case.
- `TestCreateRoutesLabelNotesThroughMakeTsString` -- `Create()` with
  and without label/notes, including the pre-existing-safe
  `if label:`/`if notes:` empty-string guard branch.

The mock `IConstChartRow.Label`/`.Notes` are genuine bare `ITsString`
instances built via `TsStringUtils.MakeString` (same CLR type
confirmed live), not a plain Python duck-typed stand-in -- necessary
because `BaseOperations._ReadTsString`'s `ITsString(tss)` cast raises
`TypeError` ("object does not implement ITsString") on anything that
doesn't really implement the interface, so a duck-typed fake could not
exercise the real getter code path. This only needs the loaded
`SIL.LCModel` assembly, not an open project -- the same unmarked usage
pattern already present elsewhere in this suite (e.g.
`tests/test_lcm_api_real.py`, `tests/test_lcm_direct.py`). A minimal
`_MockFLExProject`/`_MockLcmCache`/`_MockServiceLocator`/
`_MockRowFactory`/`_MockRowsOS` scaffold supplies just enough surface
for `_EnsureWriteEnabled`, `_TransactionCM` (Phase 1/non-undoable
path), and the `IConstChartRowFactory` service-locator call in
`Create()` to run without a live LCM session.

## Test run

```
python -m pytest tests/operations/test_290_const_chart_row_tsstring.py -q
```
Result: 13 passed.

Also ran together with the sibling #299/#300 regression files to
confirm no interference:
```
python -m pytest tests/operations/test_290_const_chart_row_tsstring.py tests/operations/test_300_getsequence_property_rename.py tests/operations/test_299_getsequence_ownership_fix.py -q
```
Result: 28 passed.

Confirmed via `--collect-only` that the untouched
`tests/operations/test_issue290_const_chart_reflection.py` still
collects its original 3 tests unchanged.

No live tests were run this cycle (out of scope per dispatch
instructions -- a separate agent owns the live session).

## Files changed

- `flexicon/code/Discourse/ConstChartRowOperations.py` (the fix)
- `tests/operations/test_290_const_chart_row_tsstring.py` (new, mock
  regression tests)

Changes are left uncommitted in the working tree per instructions.
